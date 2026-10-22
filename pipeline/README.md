# Human-supervised CISS extraction pilot

This public snapshot searches OpenAlex, requires human candidate screening, sends
user-supplied PDFs to Gemini, and validates returned JSON locally. Source PDFs,
credentials and raw API responses are not distributed.

## Files

- `pilot.py`: search, filter, extract and validate commands.
- `schema.json`: historical v0.4.0 schema.
- `schema_v0.5.0.json`: project compatibility extension for v0.5.0.
- `extraction_prompt.txt`: source-grounded extraction instructions.
- `queries.json`: default literature queries.
- `examples/cuo_pilot.json`: partial, pending-review CuO source-reading example.
- `examples/cuo_validation.json`: local structural/provenance validation output;
  review flags require human attention and are not approval.

## Setup and offline validation

From the repository root, first run `cd pipeline`. Then, with Python 3.10 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pilot.py validate examples/cuo_pilot.json
```

Validation requires no API key and makes no API requests. Dependencies in
`requirements.txt` specify minimum versions, not a fully pinned environment.

## Search and screen

```sh
python pilot.py search --query 'chiral CuO spin polarized photoemission' --out runs/search
```

Search uses OpenAlex; an optional `OPENALEX_API_KEY` is read from the environment.
Inspect `runs/search/candidates.json`. For a selected candidate, set `decision` to
`include`, fill in `reason` and `reviewer`, supply a local `main_pdf` path, and set
`si_status` to `available`, `unavailable`, or `none_confirmed`. If available, also
supply `si_pdf`. Obtain PDFs yourself with appropriate access. No PDF is downloaded
by this program. Search results and generated files stay local unless you publish them.

## Optional live extraction

Set `GEMINI_API_KEY` privately in your environment. Choose a Gemini model supporting
PDF input and JSON output, then replace the DOI and model placeholders:

```sh
python pilot.py extract --candidates runs/search/candidates.json --doi YOUR_DOI --model YOUR_MODEL --out runs/new_run --schema-version 0.5.0
python pilot.py validate runs/new_run/draft.json
```

This sends the selected PDFs and candidate metadata to Gemini and can incur API
charges. Combined inline PDFs must be smaller than 10 MB. Output directories must
be new. Use `--schema-version 0.4.0` for historical extraction. Outputs include a
manifest, raw response, draft and validation report; no record is automatically
approved. Manifests contain local document paths and are not intended for blind publication.

## Interpretation

The CuO example is a selected-value source-reading pilot, not a new Gemini run.
The v0.5.0 schema is a project compatibility extension. Structural validation cannot
prove evidence accuracy, completeness, uncertainty interpretation or scientific
comparability. Review the paper, signs, units, sample links and omissions manually.

## Export the published six-paper dataset

The separate export step does not require live extraction or an API key.
From this `pipeline/` directory:

```sh
python ../dataset/build_dataset.py
```

Outputs appear in `../dataset/`. See the [dataset README](../dataset/README.md)
for generated files, inclusion rules and the distinction between export labels
and human review. For a complete starting sequence, see the [root README](../README.md#run-the-pipeline).
