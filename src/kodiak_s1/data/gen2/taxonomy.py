"""The v2 taxonomy: sectors -> domains -> document types (each with the state formats that fit).

Generated once by the writer model, skimmed by a human, then versioned in git (data/gen2/taxonomy_v2.json).
The *sectors* are hand-written here so coverage is broad by construction (the Jev goal: as many task domains as
we can get); the model only fills in domains and document types inside each sector.

The cross-cutting axes (decision types, scales, difficulty, null kinds) are NOT generated; they live in specs.py,
where they can be read and reviewed as code.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TAXONOMY_PATH = Path("data/gen2/taxonomy_v2.json")
FORMATS = ("text", "list", "json")

SECTORS = [
    "commerce, retail and e-commerce",
    "banking, payments, insurance and personal finance",
    "healthcare administration, pharmacy logistics and wellness (no diagnosis)",
    "software engineering, IT operations and DevOps",
    "cybersecurity, fraud and trust & safety",
    "government, legal, compliance and civic services",
    "education, academic research and libraries",
    "media, publishing, entertainment and games",
    "travel, hospitality, transportation and logistics",
    "real estate, construction and facilities management",
    "human resources, recruiting and the workplace",
    "manufacturing, energy, utilities and IoT",
    "personal life, households and community organizations",
    "automotive, vehicles and repair",
    "agriculture, environment and the natural sciences",
    "AI assistants, chatbots and tool-using agents",
]


def taxonomy_prompt(sector: str, n_domains: int) -> str:
    return f"""We are building a broad taxonomy of settings where an automated decision system reads a document or record
and answers questions about it (classify it, route it, score it, check it, pick the next action).

Sector: {sector}

List {n_domains} distinct domains (specific sub-areas) inside this sector. Make them concrete and varied: cover
consumer and business settings, large and small organizations, routine and unusual situations. Avoid overlapping domains.
For each domain, give 3 to 6 document types that a system in that domain really reads: concrete artifacts such as
'warranty claim form', 'driver dispatch chat', 'nightly backup job log', 'tenant noise complaint email'.
For each document type, list the formats it naturally comes in:
- "text": a single prose document or message
- "list": several separate texts in order (messages in a thread, entries, several short documents)
- "json": a structured record a software system would emit
Return JSON only."""


def taxonomy_schema(n_domains: int) -> dict:
    doc_type = {"type": "object", "properties": {
        "name": {"type": "string"},
        "formats": {"type": "array", "items": {"type": "string", "enum": list(FORMATS)}, "minItems": 1, "maxItems": 3}},
        "required": ["name", "formats"]}
    domain = {"type": "object", "properties": {
        "name": {"type": "string"},
        "doc_types": {"type": "array", "items": doc_type, "minItems": 3, "maxItems": 6}},
        "required": ["name", "doc_types"]}
    return {"type": "object", "properties": {
        "domains": {"type": "array", "items": domain, "minItems": n_domains, "maxItems": n_domains}},
        "required": ["domains"]}


def _clean(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip().strip(".")[:120]


def normalize(sectors: dict[str, list[dict]]) -> dict:
    """Drop duplicates (across sectors too), empty names and unknown formats; keep domains with >= 2 doc types."""
    out, seen_domains = [], set()
    for sector, domains in sectors.items():
        kept = []
        for d in domains:
            name = _clean(d.get("name", ""))
            if not name or name.casefold() in seen_domains:
                continue
            docs, seen_docs = [], set()
            for dt in d.get("doc_types") or []:
                dn = _clean(dt.get("name", ""))
                fmts = [f for f in dict.fromkeys(dt.get("formats") or []) if f in FORMATS]
                if dn and fmts and dn.casefold() not in seen_docs:
                    seen_docs.add(dn.casefold())
                    docs.append({"name": dn, "formats": fmts})
            if len(docs) >= 2:
                seen_domains.add(name.casefold())
                kept.append({"name": name, "doc_types": docs})
        out.append({"name": sector, "domains": kept})
    return {"version": "v2", "sectors": out}


def generate(model: str, n_domains: int = 20, workers: int = 8) -> dict:
    from kodiak_s1.data import synth

    def one(sector: str) -> list[dict]:
        for attempt in range(3):
            try:
                r = synth.teacher(taxonomy_prompt(sector, n_domains), taxonomy_schema(n_domains), 0.7, model, 6000)
                return r["content"]["domains"]
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                if attempt == 2:
                    raise
        return []

    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(one, SECTORS))
    tax = normalize(dict(zip(SECTORS, results)))
    tax["writer"] = model
    return tax


def load(path: str | Path = TAXONOMY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cells(tax: dict) -> list[tuple[str, str, str, tuple[str, ...]]]:
    """Every (sector, domain, doc_type, formats) combination, in file order (deterministic)."""
    return [(s["name"], d["name"], dt["name"], tuple(dt["formats"]))
            for s in tax["sectors"] for d in s["domains"] for dt in d["doc_types"]]


def summary(tax: dict) -> str:
    n_dom = sum(len(s["domains"]) for s in tax["sectors"])
    lines = [f"{len(tax['sectors'])} sectors, {n_dom} domains, {len(cells(tax))} document types"]
    for s in tax["sectors"]:
        lines.append(f"  {s['name']}: {len(s['domains'])} domains")
    return "\n".join(lines)
