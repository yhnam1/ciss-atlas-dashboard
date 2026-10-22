# CISS Atlas Dashboard

[Open the dashboard](https://yhnam1.github.io/ciss-atlas-dashboard/)

A standalone CISS literature dashboard covering six papers, structured measurements,
source evidence and human-supervised extraction pilot results.
No installation, account or API key is needed to view it. Download `index.html`
and open it in a browser for offline use.

## Public source package

The [pipeline](pipeline/) contains the extraction and validation code, both schema
versions, extraction prompt, search queries, dependencies and one example with
its local validation report. See [pipeline instructions](pipeline/README.md).
The [public dataset](dataset/) provides all six paper JSON records, explicit human
review status, file hashes and local validation results. Three records have completed
expert review and three remain pending.

The dashboard HTML contains its own display code and embedded dataset. This curated
package does not include the private dashboard build system or source PDFs.

## Run the pipeline

Use Python 3.10 or newer. The commands below start from the repository root.

```sh
git clone https://github.com/yhnam1/ciss-atlas-dashboard.git
cd ciss-atlas-dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r pipeline/requirements.txt
```

On Windows, use `python` instead of `python3` to create the environment and
`.venv\Scripts\Activate.ps1` in PowerShell to activate it.

### 1. Reproduce the dataset export (offline)

```sh
python dataset/build_dataset.py
```

This reads the six files in `dataset/records/` and generates `measurements_demo.csv`,
`all_entries.csv`, `papers.csv`, `dataset.jsonl` and `summary.json` inside `dataset/`.
It uses only the Python standard library: package installation and API keys are
not needed for this step. Re-running overwrites these generated exports, not the
source records. With this snapshot, expect **6 papers, 131 entries and 85 numeric
photoelectron-spin rows**. The rows include controls and are not necessarily
independent observations. See [dataset details](dataset/README.md).

The exporter preserves its historical `review_status=unreviewed_draft` label;
consult `dataset/review_status.json` for the separate, hash-scoped human review
status. Exporting does not approve records or rebuild the dashboard HTML.

### 2. Validate an existing record (offline)

```sh
python pipeline/pilot.py validate dataset/records/cuo_pilot.json
```

No API key is needed. This example has zero validation errors but human-review
flags remain. Other records may return validation errors; see the published
[validation report](dataset/validation_report.json). Validation is not scientific approval.

### 3. Search, screen and extract a new paper (optional, online)

```sh
cd pipeline
python pilot.py search --query 'chiral CuO spin polarized photoemission' --out runs/search
```

Edit `runs/search/candidates.json`: for the chosen DOI, set `decision` to `include`,
fill in `reason` and `reviewer`, and set `main_pdf` to your local PDF path.
Set `si_status` to `available`, `unavailable` or `none_confirmed`; if available,
also set `si_pdf`. Relative PDF paths are resolved from the current working directory.
The program does not download PDFs. Search can read `OPENALEX_API_KEY` from your environment.

Set `GEMINI_API_KEY` privately in your environment, then replace `YOUR_DOI` and
`YOUR_MODEL` with the screened DOI and a Gemini model supporting PDFs and JSON output:

```sh
python pilot.py extract --candidates runs/search/candidates.json --doi YOUR_DOI --model YOUR_MODEL --out runs/new_run --schema-version 0.5.0
python pilot.py validate runs/new_run/draft.json
```

Extraction sends supplied PDFs and candidate metadata to Gemini and may incur
API charges. Search and extraction output directories must be new; use different
names for repeat runs. Combined inline PDFs must be below 10 MB.
The output is an unreviewed draft, not an automatically approved dataset addition.
Inspect the validation report and review the original sources before incorporating
any new record. This does not update the hosted dashboard automatically.
See [full pipeline instructions](pipeline/README.md) for output files and limitations.

## Review status and limitations

Seed papers 1–3 have completed expert review, as confirmed by the project owner.
Paper 4, the CuO and tetrapyrrole pilots, and alternative API drafts remain pending
review. The CuO example is a partial source-reading pilot, not evidence of a new
API extraction. Schema validity does not establish scientific accuracy or completeness.
The v0.5.0 schema is a project compatibility extension, not an externally validated
canonical standard. Historical v0.4.0 records retain their original schema.

## Submission links

- Demo: https://yhnam1.github.io/ciss-atlas-dashboard/
- Code: https://github.com/yhnam1/ciss-atlas-dashboard

Only the generated dashboard HTML is refreshed by the existing dashboard publisher.
The public pipeline and standalone dataset are curated snapshots and must be updated separately.
