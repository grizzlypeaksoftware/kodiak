// JavaScript vs Python parity on shared fixtures (test/fixtures/parity.json, written from the Python package).
// Packing must match token for token; answers must match to within float noise.
//
//   KODIAK_MODEL=../runs/onnx/kodiak-small-v2 npm test     (skips the model tests if the folder has no model.onnx)

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { betaQuantile, Kodiak, normalizeRequest, Packer, RequestError } from "../src/kodiak.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const { cases } = JSON.parse(fs.readFileSync(path.join(here, "fixtures", "parity.json"), "utf8"));
const folder = process.env.KODIAK_MODEL || path.join(here, "..", "..", "runs", "onnx", "kodiak-small-v2");
const haveModel = fs.existsSync(path.join(folder, "model.onnx"));
const tokenizerPath = path.join(folder, "tokenizer.json");

test("packing matches Python token for token", { skip: !fs.existsSync(tokenizerPath) }, () => {
  const packer = new Packer(JSON.parse(fs.readFileSync(tokenizerPath, "utf8")));
  for (const [i, c] of cases.entries()) {
    const p = packer.pack(normalizeRequest(c.request));
    for (const k of ["ids", "pos", "role", "qi", "li"]) assert.deepEqual(p[k], c[k], `case ${i}: ${k}`);
  }
});

test("Beta quantiles match scipy", () => {
  // scipy.stats.beta.ppf values
  assert.ok(Math.abs(betaQuantile(0.05, 2, 5) - 0.06284989) < 1e-6);
  assert.ok(Math.abs(betaQuantile(0.95, 2, 5) - 0.58180341) < 1e-6);
  assert.ok(Math.abs(betaQuantile(0.5, 0.5, 0.5) - 0.5) < 1e-6);
  assert.ok(Math.abs(betaQuantile(0.05, 30, 3) - 0.81605653) < 1e-6);
});

test("bad requests are rejected like the Python schema", () => {
  const q = { type: "choice", id: "a", text: "?", labels: ["x", "y"] };
  assert.throws(() => normalizeRequest({ state: "s", questions: [q, q] }), RequestError);
  assert.throws(() => normalizeRequest({ state: "s", questions: [{ ...q, labels: ["x"] }] }), RequestError);
  assert.throws(() => normalizeRequest({ state: "s", questions: [{ ...q, labels: ["Yes", "yes "] }] }), RequestError);
  assert.throws(() => normalizeRequest({ state: "s", questions: [{ type: "score", id: "s", text: "?", min: 5, max: 1 }] }), RequestError);
  assert.throws(() => normalizeRequest({ state: "s", questions: [{ id: "a", text: "?", labels: ["x", "y"] }] }), RequestError);
  assert.throws(() => normalizeRequest({ state: "s", questions: [q], extra: 1 }), RequestError);
});

function assertAnswersClose(got, want, where) {
  assert.deepEqual(Object.keys(got).sort(), Object.keys(want).sort(), where);
  for (const [qid, w] of Object.entries(want)) {
    const g = got[qid];
    const at = `${where} ${qid}`;
    assert.equal(g.abstain_reason, w.abstain_reason, `${at} abstain_reason`);
    assert.ok(Math.abs(g.p_null - w.p_null) < 1e-4, `${at} p_null ${g.p_null} vs ${w.p_null}`);
    if (w.type === "choice") {
      assert.equal(g.answer, w.answer, `${at} answer`);
      for (const [lab, p] of Object.entries(w.probs)) assert.ok(Math.abs(g.probs[lab] - p) < 1e-4, `${at} probs[${lab}]`);
    } else {
      const tol = 1e-3 * Math.max(1, Math.abs(w.mean));
      assert.ok(Math.abs(g.mean - w.mean) < tol, `${at} mean ${g.mean} vs ${w.mean}`);
      assert.ok(Math.abs(g.std - w.std) < tol, `${at} std`);
      assert.ok(Math.abs(g.interval[0] - w.interval[0]) < tol && Math.abs(g.interval[1] - w.interval[1]) < tol, `${at} interval`);
      if (w.answer === null) assert.equal(g.answer, null);
      else assert.ok(Math.abs(g.answer - w.answer) < tol, `${at} answer`);
    }
  }
}

test("answers match Python, one request at a time and packed together", { skip: !haveModel }, async () => {
  const kodiak = await Kodiak.load(folder);
  for (const [i, c] of cases.entries()) assertAnswersClose((await kodiak.answer([c.request]))[0].answers, c.response, `case ${i}`);
  const all = await kodiak.answer(cases.map((c) => c.request));
  all.forEach((r, i) => assertAnswersClose(r.answers, cases[i].response, `batched case ${i}`));
});
