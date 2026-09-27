# Kodiak server (Node.js + ONNX Runtime)

Run Kodiak on your own machine or VPS: CPU only, no Python, no GPU. It exposes the same request and response contract as the
Python package and the Hugging Face handler (JSON Schemas in [`schema/`](../schema)).

| Model | ONNX size | CPU latency, 1 request (8 threads, p50) | RAM |
|---|---|---|---|
| kodiak-small-v2 | 610 MB | ~30 ms | ~1 GB |
| kodiak-large-v2 | 1.6 GB | ~80 ms | ~2.5 GB |

Measured on an ARM64 DGX Spark with a training job running alongside; a two-question request with a short state. Longer states cost more.

## 1. Get a model folder

A model folder holds `model.onnx`, `tokenizer.json` and `calibration.json`. Build one from a published model (needs the Python package once):

```bash
uv run python -m kodiak_s1.onnx_export export --folder dist/kodiak-small-v2      # writes dist/kodiak-small-v2/model.onnx
```

The export checks that the ONNX graph matches PyTorch on fixture requests and refuses to finish if it doesn't.

## 2. Run it

```bash
cd server && npm ci
KODIAK_MODEL=../dist/kodiak-small-v2 npm start           # listens on :8080
```

or with Docker (build from the repository root):

```bash
docker build -f server/Dockerfile -t kodiak-server .
docker run -p 8080:8080 -v $PWD/dist/kodiak-small-v2:/model:ro -e KODIAK_MODEL_NAME=kodiak-small-v2 kodiak-server
```

Settings: `KODIAK_MODEL` (folder), `PORT` (8080), `KODIAK_MODEL_NAME` (reported in responses), `KODIAK_THREADS` (CPU threads,
default: all), `KODIAK_MAX_BATCH` (requests per call, default 32).

## 3. Call it

```bash
curl -s localhost:8080/v1/decide -H 'content-type: application/json' -d '{
  "state": {"order_id": "A-1042", "status": "delivered", "message": "The box arrived crushed and the lamp is broken."},
  "questions": [
    {"type": "choice", "id": "intent", "text": "What does the customer want?",
     "labels": ["refund or replacement", "delivery status", "cancel order", "product question"]},
    {"type": "choice", "id": "carrier", "text": "Which carrier delivered it?", "labels": ["UPS", "FedEx", "USPS"]}]}'
```

`intent` comes back with an answer and probabilities; `carrier` abstains (`"abstain_reason": "unanswerable"`) because the state
doesn't say. Send `{"requests": [...]}` to answer several states in one call. `GET /health` reports the model and its calibration.

From JavaScript, skip HTTP entirely:

```js
import { Kodiak } from "./src/kodiak.js";
const kodiak = await Kodiak.load("../dist/kodiak-small-v2");
await kodiak.decide("I was charged twice!", [{ type: "choice", id: "intent", text: "What does the customer want?", labels: ["refund", "track order"] }]);
```

## How it matches the Python model

- The ONNX graph takes the packed tokens and their roles and builds Kodiak's attention mask inside the graph, so the client only
  tokenizes and packs. Calibration temperatures are baked into the weights.
- `src/kodiak.js` reimplements packing, the decision rule and Beta intervals. `npm test` checks it against fixtures written by the
  Python package (`test/fixtures/parity.json`, 44 requests including 40 from the eval set). Packing must match token for token, and
  probabilities to 1e-4.
- One known difference: a JSON state with a float like `1.0` renders as `1` in JavaScript (JSON parsing drops the `.0`), so its tokens
  differ slightly from Python's.

**Not shipped: int8 quantization.** Dynamic int8 made the model ~2× faster and half the size but changed 11 of 41 choice answers on
the parity fixtures and moved abstain probabilities by up to 0.58, which breaks calibration. Per-channel variants were no better.
