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

## References

The six source papers used in this dataset are listed below. Please cite the
relevant original papers when reusing their experimental results. Each entry links
to the publisher through its DOI and to the corresponding structured JSON record.
Supporting information was also consulted, as recorded in each JSON file.

1. **DNA.** B. Göhler; V. Hamelbeck; T. Z. Markus; M. Kettner; G. F. Hanne; Z. Vager; R. Naaman; H. Zacharias (2011). Spin Selectivity in Electron Transmission Through Self-Assembled Monolayers of Double-Stranded DNA. *Science*, **331**(6019), 894–897. [DOI: 10.1126/science.1199339](https://doi.org/10.1126/science.1199339). [Dataset JSON](dataset/records/paper_1_v0.4.json).

2. **Helicenes.** Matthias Kettner; Volodymyr V. Maslyuk; Daniel Nürenberg; Johannes Seibel; Rafael Gutierrez; Gianaurelio Cuniberti; Karl-Heinz Ernst; Helmut Zacharias (2018). Chirality-Dependent Electron Spin Filtering by Molecular Monolayers of Helicenes. *The Journal of Physical Chemistry Letters*, **9**(8), 2025–2030. [DOI: 10.1021/acs.jpclett.8b00208](https://doi.org/10.1021/acs.jpclett.8b00208). [Dataset JSON](dataset/records/paper_2_v0.4.json).

3. **Bacteriorhodopsin.** Debabrata Mishra; Tal Z. Markus; Ron Naaman; Matthias Kettner; Benjamin Göhler; Helmut Zacharias; Noga Friedman; Mordechai Sheves; Claudio Fontanesi (2013). Spin-dependent electron transmission through bacteriorhodopsin embedded in purple membrane. *Proceedings of the National Academy of Sciences*, **110**(37), 14872–14876. [DOI: 10.1073/pnas.1311493110](https://doi.org/10.1073/pnas.1311493110). [Dataset JSON](dataset/records/paper_3_v0.4.json).

4. **Double-stranded PNA.** Paul Valerian Möllers; Selma Ulku; Dilhara Jayarathna; Francesco Tassinari; Daniel Nürenberg; Ron Naaman; Catalina Achim; Helmut Zacharias (2021). Spin-selective electron transmission through self-assembled monolayers of double-stranded peptide nucleic acid. *Chirality*, **33**(2), 93–102. [DOI: 10.1002/chir.23290](https://doi.org/10.1002/chir.23290). [Dataset JSON](dataset/records/paper_4_v0.4.json).

5. **Chiral CuO.** Paul V. Möllers; Jimeng Wei; Soma Salamon; Manfred Bartsch; Heiko Wende; David H. Waldeck; Helmut Zacharias (2022). Spin-Polarized Photoemission from Chiral CuO Catalyst Thin Films. *ACS Nano*, **16**(8), 12145–12155. [DOI: 10.1021/acsnano.2c02709](https://doi.org/10.1021/acsnano.2c02709). [Dataset JSON](dataset/records/cuo_pilot.json).

6. **Helical tetrapyrroles.** Paul V. Möllers; Adrian J. Urban; Steven De Feyter; Hiroshi M. Yamamoto; Helmut Zacharias (2024). Probing the Roles of Temperature and Cooperative Effects in Chirality-Induced Spin Selectivity: Photoelectron Spin Polarization in Helical Tetrapyrroles. *The Journal of Physical Chemistry Letters*, **15**(38), 9620–9629. [DOI: 10.1021/acs.jpclett.4c02209](https://doi.org/10.1021/acs.jpclett.4c02209). [Dataset JSON](dataset/records/tetrapyrrole_pilot.json).
