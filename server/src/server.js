#!/usr/bin/env node
// Self-hosted Kodiak: an HTTP API over the ONNX model. No Python, no GPU.
//
//   KODIAK_MODEL=path/to/model-folder PORT=8080 node src/server.js
//   optional: KODIAK_MODEL_NAME (reported in responses), KODIAK_THREADS (CPU threads), KODIAK_MAX_BATCH (default 32)
//
//   POST /v1/decide   one Request, or {"requests": [...]}  -> Response, or {"responses": [...]}
//   GET  /health      model name and calibration
//
// Request and Response shapes are the JSON Schemas in schema/ (the same contract as the Python package and the Hugging Face handler).

import express from "express";
import { Kodiak, RequestError } from "./kodiak.js";

const folder = process.env.KODIAK_MODEL;
if (!folder) {
  console.error("set KODIAK_MODEL to a model folder containing model.onnx, tokenizer.json and calibration.json");
  process.exit(1);
}
const port = Number(process.env.PORT || 8080);
const maxBatch = Number(process.env.KODIAK_MAX_BATCH || 32);

const kodiak = await Kodiak.load(folder, { threads: Number(process.env.KODIAK_THREADS || 0), name: process.env.KODIAK_MODEL_NAME });
const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req, res) => res.json({ status: "ok", model: kodiak.name, calibration: kodiak.calibration }));

app.post("/v1/decide", async (req, res) => {
  const body = req.body;
  const batch = Array.isArray(body?.requests);
  const requests = batch ? body.requests : [body];
  if (requests.length === 0 || requests.length > maxBatch) {
    return res.status(400).json({ error: `send between 1 and ${maxBatch} requests` });
  }
  try {
    const responses = await kodiak.answer(requests);
    res.json(batch ? { responses } : responses[0]);
  } catch (e) {
    if (e instanceof RequestError) return res.status(400).json({ error: e.message });
    console.error(e);
    res.status(500).json({ error: "inference failed" });
  }
});

// Malformed JSON bodies land here.
app.use((err, _req, res, _next) => res.status(err.status || 500).json({ error: err.message }));

app.listen(port, () => console.log(`kodiak ${kodiak.name} listening on :${port}`));
