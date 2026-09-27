// Kodiak in Node.js: the JavaScript twin of kodiak_s1.packing + kodiak_s1.infer (docs/ARCHITECTURE.md §12).
//
//   import { Kodiak } from "./kodiak.js";
//   const kodiak = await Kodiak.load("path/to/model-folder");   // model.onnx, tokenizer.json, calibration.json
//   const res = await kodiak.answer([{ state: "...", questions: [...] }]);
//
// The ONNX graph returns calibrated raw heads; everything that turns them into answers (grouped softmax, abstain rule,
// Beta summaries) lives here and is tested against the Python implementation on shared fixtures (test/parity.test.js).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Tokenizer } from "@huggingface/tokenizers";
import Ajv from "ajv/dist/2020.js";
import * as ort from "onnxruntime-node";

const PAD = 0, STATE = 1, QUESTION = 2, LABEL = 3;
const CHOICE = 0, SCORE = 1;
export const LIMITS = { maxState: 2048, maxQuestion: 128, maxLabel: 32, maxRow: 4096 };
const MARKERS = { choice: "[unused0]", score: "[unused1]", label: "[unused2]" };

const here = path.dirname(fileURLToPath(import.meta.url));
const requestSchema = JSON.parse(fs.readFileSync(path.join(here, "..", "..", "schema", "kodiak-request.schema.json"), "utf8"));
const validateSchema = new Ajv({ allErrors: true, strict: false }).compile(requestSchema);

export class RequestError extends Error {}

// ---------------------------------------------------------------------------
// Requests: the same normalization and checks as kodiak_s1.schema.Request
// ---------------------------------------------------------------------------

export function normalizeRequest(req) {
  if (!req || typeof req !== "object" || Array.isArray(req)) throw new RequestError("request must be an object");
  const r = structuredClone(req);
  for (const q of Array.isArray(r.questions) ? r.questions : []) {
    if (q && Array.isArray(q.labels)) q.labels = q.labels.map((x) => (typeof x === "string" ? { id: x, text: x } : x));
  }
  if (!validateSchema(r)) {
    const msg = validateSchema.errors.map((e) => `${e.instancePath || "/"} ${e.message}`).join("; ");
    throw new RequestError(`invalid request: ${msg}`);
  }
  // Python's discriminated union needs an explicit type; the generated JSON Schema only gives it a default.
  if (r.questions.some((q) => q.type !== "choice" && q.type !== "score")) throw new RequestError('every question needs "type": "choice" or "score"');
  const ids = r.questions.map((q) => q.id);
  if (new Set(ids).size !== ids.length) throw new RequestError("question ids must be unique");
  for (const q of r.questions) {
    q.allow_null = q.allow_null ?? true;
    if (q.type === "choice") {
      const lids = q.labels.map((l) => l.id), texts = q.labels.map((l) => l.text.trim().toLowerCase());
      if (new Set(lids).size !== lids.length) throw new RequestError("label ids must be unique within a question");
      if (new Set(texts).size !== texts.length) throw new RequestError("label texts must be distinct within a question");
    } else {
      q.min = q.min ?? 0; q.max = q.max ?? 1;
      if (!(Number.isFinite(q.min) && Number.isFinite(q.max)) || q.min >= q.max) throw new RequestError("score range requires finite min < max");
    }
  }
  r.options = { null_threshold: 0.5, min_confidence: 0, interval: 0.9, ...(r.options || {}) };
  return r;
}

export function renderState(state) {
  if (typeof state === "string") return state;
  if (Array.isArray(state) && state.every((x) => typeof x === "string")) return state.map((x, i) => `[${i + 1}] ${x}`).join("\n");
  // Python writes json.dumps(state, ensure_ascii=False, separators=(",", ":")). Identical except for floats with a zero fraction
  // (Python "1.0", JavaScript "1"), which JSON parsing has already erased by the time a request reaches us.
  return JSON.stringify(state);
}

export function questionText(q) {
  if (q.type === "score" && (q.min_label || q.max_label)) return `${q.text} (min: ${q.min_label || "lowest"}; max: ${q.max_label || "highest"})`;
  return q.text;
}

// ---------------------------------------------------------------------------
// Packing: one request -> tokens with roles (kodiak_s1.packing.pack_example)
// ---------------------------------------------------------------------------

export class Packer {
  constructor(tokenizerJson, limits = LIMITS) {
    this.tok = new Tokenizer(tokenizerJson, {});
    this.limits = limits;
    const id = (s) => tokenizerJson.added_tokens.find((t) => t.content === s).id;
    this.special = { cls: id("[CLS]"), sep: id("[SEP]"), pad: id("[PAD]"), choice: id(MARKERS.choice), score: id(MARKERS.score), label: id(MARKERS.label) };
  }

  encode(text) {
    return this.tok.encode(text, { add_special_tokens: false }).ids;
  }

  pack(req) {
    const L = this.limits;
    let truncated = false;
    let state = this.encode(renderState(req.state));
    if (state.length > L.maxState - 2) { state = state.slice(0, L.maxState - 2); truncated = true; }
    const ids = [this.special.cls, ...state, this.special.sep];
    const S = ids.length;
    const p = { ids, pos: [...Array(S).keys()], role: Array(S).fill(STATE), qi: Array(S).fill(-1), li: Array(S).fill(-1),
      qOff: [], qType: [], qAllowNull: [], lOff: [], lQ: [], qids: [], labelIds: [], truncated };
    req.questions.forEach((q, i) => {
      let qt = [q.type === "choice" ? this.special.choice : this.special.score, ...this.encode(questionText(q))];
      if (qt.length > L.maxQuestion) { qt = qt.slice(0, L.maxQuestion); p.truncated = true; }
      p.qOff.push(p.ids.length); p.qType.push(q.type === "choice" ? CHOICE : SCORE); p.qAllowNull.push(q.allow_null !== false); p.qids.push(q.id);
      push(p, qt, S, QUESTION, i, -1);
      const labelStart = S + qt.length;
      const labels = q.type === "choice" ? q.labels : [];
      p.labelIds.push(labels.map((l) => l.id));
      labels.forEach((lab, j) => {
        let lt = [this.special.label, ...this.encode(lab.text)];
        if (lt.length > L.maxLabel) { lt = lt.slice(0, L.maxLabel); p.truncated = true; }
        p.lOff.push(p.ids.length); p.lQ.push(i);
        push(p, lt, labelStart, LABEL, i, j);
      });
    });
    return p;
  }

  // Greedy packing of several requests into rows (kodiak_s1.packing.collate). Returns ONNX feeds plus bookkeeping.
  collate(packed) {
    const rows = [[]], used = [0];
    packed.forEach((p, k) => {
      if (p.ids.length > this.limits.maxRow) throw new RequestError(`request ${k} is ${p.ids.length} tokens; the limit is ${this.limits.maxRow}`);
      if (used.at(-1) + p.ids.length > this.limits.maxRow) { rows.push([]); used.push(0); }
      rows.at(-1).push(k); used[used.length - 1] += p.ids.length;
    });
    const B = rows.length, N = Math.max(...used);
    const t = {}, fill = { input_ids: this.special.pad, pos: 0, doc: -1, role: PAD, qi: -1, li: -1 };
    for (const [name, v] of Object.entries(fill)) t[name] = new BigInt64Array(B * N).fill(BigInt(v));
    const qRow = [], qCol = [], lRow = [], lCol = [], lQ = [], qExample = [];
    rows.forEach((members, r) => {
      let off = 0;
      members.forEach((k, d) => {
        const p = packed[k];
        for (let n = 0; n < p.ids.length; n++) {
          const at = r * N + off + n;
          t.input_ids[at] = BigInt(p.ids[n]); t.pos[at] = BigInt(p.pos[n]); t.doc[at] = BigInt(d);
          t.role[at] = BigInt(p.role[n]); t.qi[at] = BigInt(p.qi[n]); t.li[at] = BigInt(p.li[n]);
        }
        const qBase = qRow.length;
        p.qOff.forEach((o) => { qRow.push(r); qCol.push(off + o); qExample.push(k); });
        p.lOff.forEach((o, j) => { lRow.push(r); lCol.push(off + o); lQ.push(qBase + p.lQ[j]); });
        off += p.ids.length;
      });
    });
    // Padding gets its own far-away position so it never falls inside a real token's local attention window.
    for (let i = 0; i < B * N; i++) if (t.doc[i] < 0n) t.pos[i] = 1000000n;
    const big = (a) => BigInt64Array.from(a, BigInt);
    const feeds = {};
    for (const name of ["input_ids", "pos", "doc", "role", "qi", "li"]) feeds[name] = new ort.Tensor("int64", t[name], [B, N]);
    feeds.q_row = new ort.Tensor("int64", big(qRow), [qRow.length]);
    feeds.q_col = new ort.Tensor("int64", big(qCol), [qCol.length]);
    feeds.l_row = new ort.Tensor("int64", big(lRow), [lRow.length]);
    feeds.l_col = new ort.Tensor("int64", big(lCol), [lCol.length]);
    feeds.l_q = new ort.Tensor("int64", big(lQ), [lQ.length]);
    return { feeds, lQ, qExample };
  }
}

function push(p, toks, start, role, qi, li) {
  toks.forEach((id, n) => { p.ids.push(id); p.pos.push(start + n); p.role.push(role); p.qi.push(qi); p.li.push(li); });
}

// ---------------------------------------------------------------------------
// The decision rule (kodiak_s1.infer.decide)
// ---------------------------------------------------------------------------

const r6 = (x) => Math.round(x * 1e6) / 1e6;
const sigmoid = (z) => 1 / (1 + Math.exp(-z));

export function decide(raw, q, opts) {
  const pNull = raw.p_null;
  const allow = q.allow_null !== false;
  if (raw.type === "choice") {
    const probs = {};
    raw.labels.forEach((lab, i) => { probs[lab] = (1 - pNull) * raw.cond_probs[i]; });
    const best = raw.labels.reduce((a, b) => (probs[b] > probs[a] ? b : a));
    const ans = { type: "choice", probs: Object.fromEntries(Object.entries(probs).map(([k, v]) => [k, r6(v)])), p_null: r6(pNull) };
    if (allow && pNull >= opts.null_threshold) return { ...ans, answer: null, confidence: r6(pNull), abstain_reason: "unanswerable" };
    if (allow && probs[best] < opts.min_confidence) return { ...ans, answer: null, confidence: r6(probs[best]), abstain_reason: "low_confidence" };
    return { ...ans, answer: best, confidence: r6(probs[best]), abstain_reason: null };
  }
  const lo = q.min ?? 0, hi = q.max ?? 1;
  const a = raw.mu * raw.kappa, b = (1 - raw.mu) * raw.kappa;
  const stdU = Math.sqrt((a * b) / ((a + b) ** 2 * (a + b + 1)));
  const tail = (1 - opts.interval) / 2;
  const iLo = betaQuantile(tail, a, b), iHi = betaQuantile(1 - tail, a, b);
  const mean = lo + raw.mu * (hi - lo);
  let value = mean;
  if (q.step) value = lo + Math.round((value - lo) / q.step) * q.step;
  const ans = { type: "score", mean, std: stdU * (hi - lo), interval: [lo + iLo * (hi - lo), lo + iHi * (hi - lo)], p_null: r6(pNull) };
  if (allow && pNull >= opts.null_threshold) return { ...ans, answer: null, abstain_reason: "unanswerable" };
  return { ...ans, answer: value, abstain_reason: null };
}

// Beta quantiles without dependencies: regularized incomplete beta (Lentz continued fraction), inverted by bisection.
function lgamma(x) {
  const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
  let y = x, tmp = x + 5.5, ser = 1.000000000190015;
  tmp -= (x + 0.5) * Math.log(tmp);
  for (const v of c) ser += v / ++y;
  return -tmp + Math.log((2.5066282746310005 * ser) / x);
}

function betacf(x, a, b) {
  const TINY = 1e-300;
  let c = 1, d = 1 - ((a + b) * x) / (a + 1);
  if (Math.abs(d) < TINY) d = TINY;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 300; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((a + m2 - 1) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d; h *= d * c;
    aa = (-(a + m) * (a + b + m) * x) / ((a + m2) * (a + m2 + 1));
    d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 1e-15) break;
  }
  return h;
}

export function betaCdf(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const front = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log1p(-x));
  return x < (a + 1) / (a + b + 2) ? (front * betacf(x, a, b)) / a : 1 - (front * betacf(1 - x, b, a)) / b;
}

export function betaQuantile(p, a, b) {
  let lo = 0, hi = 1;
  for (let i = 0; i < 100; i++) {
    const mid = (lo + hi) / 2;
    if (betaCdf(mid, a, b) < p) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

// ---------------------------------------------------------------------------
// The model
// ---------------------------------------------------------------------------

export class Kodiak {
  constructor(session, packer, calibration = {}, name = "kodiak") {
    this.session = session;
    this.packer = packer;
    this.calibration = calibration;
    this.name = name;
    // The abstain threshold tuned on validation data is the default; a request's own options still win (as in kodiak_s1.hub).
    this.defaultOptions = { null_threshold: calibration.null_threshold ?? 0.5 };
  }

  static async load(folder, { threads = 0, name } = {}) {
    const read = (f) => JSON.parse(fs.readFileSync(path.join(folder, f), "utf8"));
    const opts = threads ? { intraOpNumThreads: threads } : {};
    const session = await ort.InferenceSession.create(path.join(folder, "model.onnx"), opts);
    const cal = fs.existsSync(path.join(folder, "calibration.json")) ? read("calibration.json") : {};
    return new Kodiak(session, new Packer(read("tokenizer.json")), cal, name || path.basename(path.resolve(folder)));
  }

  // Per request, per question: probabilities before the decision rule (kodiak_s1.infer.raw_outputs).
  async rawOutputs(requests) {
    const packed = requests.map((r) => this.packer.pack(r));
    const { feeds, lQ, qExample } = this.packer.collate(packed);
    const o = await this.session.run(feeds);
    const zChoice = o.z_choice.data, zNull = o.z_null.data, mu = o.mu.data, kappa = o.kappa.data;
    const out = requests.map(() => []);
    qExample.forEach((ex, qidx) => {
      const p = packed[ex], n = out[ex].length;
      const allow = p.qAllowNull[n];
      const rec = { qid: p.qids[n], type: p.qType[n] === CHOICE ? "choice" : "score", p_null: allow ? sigmoid(zNull[qidx]) : 0,
        z_null: zNull[qidx], allow_null: allow, truncated: p.truncated };
      if (p.qType[n] === CHOICE) {
        const z = [];
        lQ.forEach((q, j) => { if (q === qidx) z.push(zChoice[j]); });
        const m = Math.max(...z), e = z.map((v) => Math.exp(v - m)), s = e.reduce((x, y) => x + y, 0);
        rec.labels = p.labelIds[n];
        rec.cond_probs = e.map((v) => v / s);
      } else {
        rec.mu = mu[qidx];
        rec.kappa = kappa[qidx];
      }
      out[ex].push(rec);
    });
    return out;
  }

  // Full Request objects in, Response objects out (the shape kodiak_s1.infer.answer returns).
  async answer(requests) {
    const reqs = requests.map((r) => {
      const n = normalizeRequest(r);
      n.options = { ...n.options, ...this.defaultOptions, ...(r.options || {}) };
      return n;
    });
    const t0 = performance.now();
    const raws = await this.rawOutputs(reqs);
    const ms = (performance.now() - t0) / Math.max(1, reqs.length);
    return reqs.map((req, i) => {
      const qs = Object.fromEntries(req.questions.map((q) => [q.id, q]));
      const answers = Object.fromEntries(raws[i].map((r) => [r.qid, decide(r, qs[r.qid], req.options)]));
      return { model: this.name, latency_ms: Math.round(ms * 100) / 100, answers };
    });
  }

  async decide(state, questions, options) {
    return (await this.answer([{ state, questions, ...(options ? { options } : {}) }]))[0].answers;
  }
}
