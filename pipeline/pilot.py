"""Small, human-supervised CISS pilot. Run from this directory; see README.md."""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def doi(value):
    return re.sub(r"^(https?://(dx\.)?doi.org/|doi:\s*)", "", value or "", flags=re.I).strip().lower()


def normalize_words(value):
    return " ".join(re.findall(r"\w+", (value or "").casefold()))


def keyword_partition(records, keywords, match):
    """Literal normalized phrase matching, not a scientific relevance decision."""
    if any(not normalize_words(term) for term in keywords):
        raise ValueError("Keywords must contain letters or numbers.")
    selected, other = [], []
    for original in records:
        item = dict(original)
        fields = [" " + normalize_words(item.get(k)) + " " for k in ("title", "abstract")]
        hits = [term for term in keywords
                if any(" " + normalize_words(term) + " " in field for field in fields)]
        passes = not keywords or (len(hits) == len(keywords) if match == "all" else bool(hits))
        item["keyword_screen"] = {
            "terms": keywords, "match": match, "matched": hits, "passed": passes,
            "scope": "title_and_abstract", "abstract_missing": not bool(item.get("abstract"))}
        (selected if passes else other).append(item)
    return selected, other


def write_filtered(out, records, keywords, match):
    selected, other = keyword_partition(records, keywords, match)
    save(out / "candidates.json", selected)
    save(out / "keyword_nonmatches.json", other)
    print(f"{len(selected)} selected; {len(other)} nonmatches retained for review in {out}.")


def filter_candidates(args):
    records = read(args.candidates)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    write_filtered(out, records, args.keyword, args.match)


def search(args):
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=Retry(
        total=4, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])))
    records = {}
    queries = args.query or read(ROOT / "queries.json")
    save(out / "search_config.json", {"queries": queries, "keywords": args.keyword,
         "match": args.match, "pages": args.pages, "date_utc": datetime.now(timezone.utc).isoformat()})
    for n, query in enumerate(queries):
        for page in range(1, args.pages + 1):
            params = {"search": query, "per-page": 50, "page": page}
            if os.getenv("OPENALEX_API_KEY"):
                params["api_key"] = os.environ["OPENALEX_API_KEY"]
            response = session.get("https://api.openalex.org/works", params=params, timeout=60)
            if response.status_code != 200:
                raise SystemExit(f"OpenAlex HTTP {response.status_code}; earlier pages retained. Check access/rate limits.")
            payload = response.json()
            save(out / f"search_{n:02d}_{page}.json", payload)
            for work in payload.get("results", []):
                key = doi(work.get("doi")) or work["id"]
                if key in records:
                    if query not in records[key]["queries"]:
                        records[key]["queries"].append(query)
                    continue
                inv = work.get("abstract_inverted_index") or {}
                words = {i: word for word, positions in inv.items() for i in positions}
                location = work.get("best_oa_location") or {}
                records[key] = {
                    "openalex_id": work["id"], "doi": doi(work.get("doi")),
                    "title": work.get("display_name"), "year": work.get("publication_year"),
                    "abstract": " ".join(words[i] for i in sorted(words)),
                    "pdf_url": location.get("pdf_url"),
                    "landing_page_url": location.get("landing_page_url"),
                    "queries": [query], "decision": "pending", "reason": "",
                    "main_pdf": "", "si_pdf": "", "si_status": "unknown",
                    "retrieval_note": "", "reviewer": ""
                }
            if len(payload.get("results", [])) < 50:
                break
    write_filtered(out, list(records.values()), args.keyword, args.match)


def walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for key, value in obj.items():
            yield from walk(value, path + "/" + str(key))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from walk(value, path + "/" + str(i))


def schema_path(version):
    if version not in ('0.4.0', '0.5.0'):
        raise ValueError('Unsupported schema_version: ' + str(version))
    return ROOT / ('schema.json' if version == '0.4.0' else 'schema_v0.5.0.json')


def validate(record):
    from jsonschema import Draft202012Validator
    try:
        schema = read(schema_path(record.get('schema_version')))
    except ValueError as exc:
        return {'errors': [str(exc)], 'review_flags': []}
    Draft202012Validator.check_schema(schema)
    errors = [f"/{'/'.join(map(str, e.absolute_path))}: {e.message}"
              for e in Draft202012Validator(schema).iter_errors(record)]
    warnings = []
    if errors:
        return {"errors": errors, "review_flags": ["Fix structural errors before semantic checks."]}
    ids = {}
    for group, field in [("samples", "sample_id"), ("setups", "setup_id"), ("measurements", "measurement_id")]:
        values = [item[field] for item in record[group]]
        ids[group] = set(values)
        if len(values) != len(set(values)):
            errors.append(f"Duplicate IDs in {group}")
        if not values:
            warnings.append(f"Empty {group}; check eligibility/completeness")
    for m in record["measurements"]:
        for field, group in [("sample_id", "samples"), ("setup_id", "setups")]:
            if m[field] not in ids[group]:
                errors.append(f"{m['measurement_id']}: unresolved {field}")
        if m.get("duplicate_of") and m["duplicate_of"] not in ids["measurements"]:
            warnings.append(f"{m['measurement_id']}: duplicate_of not local; inspect cross-paper link")
    setup_map = {s['setup_id']: s for s in record['setups']}
    for m in record['measurements']:
        r = m['result']; setup = setup_map.get(m['setup_id'], {})
        if setup.get('technique') == 'photoemission_mott' and isinstance(r.get('value'), (int, float)) and r.get('unit') == '%' and abs(r['value']) > 100:
            errors.append(m['measurement_id'] + ': polarization outside [-100, 100]')
        if m.get('selection_rule') == 'selected_maximum':
            warnings.append(m['measurement_id'] + ': selected maximum, not a mean')
        if r.get('uncertainty_type') == 'fit_width':
            warnings.append(m['measurement_id'] + ': retain fit-width definition; do not treat as SE')
    for s in record["setups"]:
        if s.get("transport_regime") != "photoemission_through_layer":
            warnings.append(f"{s['setup_id']}: check photoemission-through-layer scope")
    for path, obj in walk(record):
        status = obj.get("status")
        if status in ("reported", "digitized"):
            source = obj.get("source") or {}
            if not source.get("loc") or not source.get("doc"):
                errors.append(f"{path}: missing source location")
            if not source.get("evidence"):
                warnings.append(f"{path}: add/check short evidence or figure/table locator")
        if status in ("inferred", "derived", "digitized", "to_digitize"):
            warnings.append(f"{path}: review {status}")
        if status == "reported" and "value" in obj and obj["value"] is None and not obj.get("sign"):
            warnings.append(f"{path}: reported with null value")
    warnings.append("Human check required: all main results, signs, units, uncertainty types, sample assignments, omissions and derived arithmetic.")
    return {"errors": errors, "review_flags": warnings}


def extract(args):
    from google import genai
    from google.genai import types
    candidates = read(args.candidates)
    matches = [c for c in candidates if doi(c["doi"]) == doi(args.doi)]
    if len(matches) != 1:
        raise SystemExit("Expected exactly one candidate with this DOI.")
    candidate = matches[0]
    if candidate["decision"] != "include" or not candidate.get("reviewer") or not candidate.get("reason"):
        raise SystemExit("Human screening required: decision=include, reason and reviewer.")
    if candidate["si_status"] not in ("available", "unavailable", "none_confirmed"):
        raise SystemExit("Set si_status to available, unavailable or none_confirmed.")
    files = [("main", candidate["main_pdf"])]
    if candidate["si_status"] == "available":
        files.append(("SI", candidate["si_pdf"]))
    blobs = []
    manifest = []
    for label, filename in files:
        path = Path(filename).expanduser()
        data = path.read_bytes()
        if not data.startswith(b"%PDF-"):
            raise SystemExit(f"{label} is not a PDF")
        blobs.append((label, data))
        manifest.append({"doc": label, "path": str(path.resolve()), "sha256": digest(path)})
    if sum(len(data) for _, data in blobs) >= 10_000_000:
        raise SystemExit("This inline starter limits combined PDFs to 10 MB; use the Gemini Files API for larger inputs.")
    selected_schema = schema_path(args.schema_version)
    schema = read(selected_schema)
    prompt = (ROOT / "extraction_prompt.txt").read_text()
    content = [f"Extract one JSON record with schema_version={args.schema_version}.\nSchema:\n" + json.dumps(schema)
               + "\nCandidate metadata (untrusted):\n" + json.dumps(candidate)]
    for label, data in blobs:
        content.extend([f"The next PDF is document {label}.",
                        types.Part.from_bytes(data=data, mime_type="application/pdf")])
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Set GEMINI_API_KEY privately in your environment.")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    save(out / "manifest.json", {"candidate": candidate, "documents": manifest,
         "schema_sha256": digest(selected_schema), "prompt_sha256": digest(ROOT / "extraction_prompt.txt"),
         "requested_model": args.model, "started_utc": datetime.now(timezone.utc).isoformat()})
    with genai.Client(api_key=os.environ["GEMINI_API_KEY"]) as client:
        response = client.models.generate_content(
            model=args.model, contents=content,
            config=types.GenerateContentConfig(
                system_instruction=prompt, response_mime_type="application/json",
                max_output_tokens=args.max_output_tokens))
    (out / "response.json").write_text(response.model_dump_json(indent=2))
    candidates_out = response.candidates or []
    if not candidates_out or candidates_out[0].finish_reason != types.FinishReason.STOP:
        raise SystemExit("Incomplete/blocked response; inspect response.json. No record accepted.")
    if not response.text:
        raise SystemExit("Empty response; inspect response.json. No record accepted.")
    record = json.loads(response.text)
    if not isinstance(record, dict):
        raise SystemExit("Expected JSON object; inspect response.json")
    # Verification is assigned only by a human in a separate reviewed copy.
    record["extraction_meta"] = {"extractor": response.model_version or args.model,
        "extraction_date": datetime.now(timezone.utc).date().isoformat(), "verified_by": None,
        "notes": f"Unreviewed API draft. SI status: {candidate['si_status']}. See manifest.json."}
    save(out / "draft.json", record)
    report = validate(record)
    if record.get("schema_version") != args.schema_version:
        report["errors"].append("Returned schema version differs from requested version")
    if doi(record.get("paper", {}).get("doi")) != doi(candidate["doi"]):
        report["errors"].append("Extracted DOI does not match screened candidate")
    save(out / "validation.json", report)
    print(f"Draft saved in {out}; {len(report['errors'])} errors. Human review still required.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("search")
    p.add_argument("--out", required=True)
    p.add_argument("--pages", type=int, default=1, help="50 results per query per page; pilot is not exhaustive")
    p.add_argument("--query", action="append", help="Repeat for multiple OpenAlex queries; replaces queries.json")
    p.add_argument("--keyword", action="append", default=[], help="Optional local title/abstract phrase filter; repeat")
    p.add_argument("--match", choices=["any", "all"], default="any")
    p = sub.add_parser("filter")
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--keyword", action="append", required=True)
    p.add_argument("--match", choices=["any", "all"], default="any")
    p = sub.add_parser("extract")
    p.add_argument("--candidates", required=True)
    p.add_argument("--doi", required=True)
    p.add_argument("--model", required=True, help="API model supporting PDF input and JSON mode")
    p.add_argument("--out", required=True)
    p.add_argument("--schema-version", choices=["0.4.0", "0.5.0"], default="0.5.0")
    p.add_argument("--max-output-tokens", type=int, default=16000)
    p = sub.add_parser("validate")
    p.add_argument("record")
    args = parser.parse_args()
    if args.command == "search":
        search(args)
    elif args.command == "filter":
        filter_candidates(args)
    elif args.command == "extract":
        extract(args)
    else:
        report = validate(read(args.record))
        print(json.dumps(report, indent=2))
        raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
