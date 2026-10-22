# Public paper records

Six structured paper records used by CISS Atlas, published unchanged from the
project dataset. These include reviewed records and pending-review pilots;
they are not all final or independently verified results.

| File | Paper | Schema | Human review |
|---|---|---|---|
| [cuo_pilot.json](records/cuo_pilot.json) | Spin-Polarized Photoemission from Chiral CuO Catalyst Thin Films | 0.5.0 | Pending review |
| [paper_1_v0.4.json](records/paper_1_v0.4.json) | Spin Selectivity in Electron Transmission Through Self-Assembled Monolayers of Double-Stranded DNA | 0.4.0 | Expert review complete |
| [paper_2_v0.4.json](records/paper_2_v0.4.json) | Chirality-Dependent Electron Spin Filtering by Molecular Monolayers of Helicenes | 0.4.0 | Expert review complete |
| [paper_3_v0.4.json](records/paper_3_v0.4.json) | Spin-dependent electron transmission through bacteriorhodopsin embedded in purple membrane | 0.4.0 | Expert review complete |
| [paper_4_v0.4.json](records/paper_4_v0.4.json) | Spin-selective electron transmission through self-assembled monolayers of double-stranded peptide nucleic acid | 0.4.0 | Pending review |
| [tetrapyrrole_pilot.json](records/tetrapyrrole_pilot.json) | Probing the Roles of Temperature and Cooperative Effects in Chirality-Induced Spin Selectivity: Photoelectron Spin Polarization in Helical Tetrapyrroles | 0.5.0 | Pending review |

Review completion for papers 1–3 follows project owner confirmation and applies
only to the exact file hashes in [review_status.json](review_status.json).
Reviewer names and completion dates were not supplied. Historical extraction
metadata is preserved; it is separate from this human-review status.

Paper 4 remains pending review. CuO and tetrapyrrole are partial, selected-value
source-reading pilots, not newly generated Gemini API runs. The v0.5.0 schema
is a project compatibility extension, not an externally validated standard.

## Validation and reuse

See [validation_report.json](validation_report.json) for current local validation
errors and review flags. Expert review status and automated validation are distinct:
reviewed historical records can still have provenance-format errors. Records were
not modified to hide these errors. Schema validity does not prove scientific
accuracy or completeness.

From the repository root after installing `pipeline/requirements.txt`:

```sh
python pipeline/pilot.py validate dataset/records/cuo_pilot.json
```

Replace the filename to validate another record. Nonzero exit status indicates
validation errors; inspect the report rather than treating every record as passed.
The six records contain 131 measurement entries, including controls, graph
placeholders and repeated evidence; this is not a count of independent observations.
Preserve source citations, uncertainty types, review status and selection rules
when reusing data. Source paper PDFs are not included.

This dataset is a curated snapshot. The dashboard publisher updates HTML only;
it does not automatically refresh these standalone JSON files. The CuO file in
`pipeline/examples/` is also retained as a standalone pipeline example.

## Rebuild the tabular exports

From the repository root:

```sh
python dataset/build_dataset.py
```

This script uses the Python standard library only and reads `dataset/records/`.
It writes or replaces the following files inside `dataset/`:

| Output | Contents |
|---|---|
| `measurements_demo.csv` | 85 eligible numeric photoelectron-spin rows |
| `all_entries.csv` | All 131 entries, including nested context encoded as JSON columns |
| `papers.csv` | Summary of the six papers |
| `dataset.jsonl` | One flattened entry per line, with nested context |
| `summary.json` | Counts, inclusion checks and per-paper summaries |

The inclusion policy is visible in `build_dataset.py`: non-spin observables,
calibration criteria, nonnumeric values, explicit duplicates, values not marked
reported and results missing source information are excluded from the numeric demo.
40 entries are graph placeholders and 6 further entries are excluded.
Generated exports retain the historical `unreviewed_draft` label. The separate
`review_status.json` records human review of the exact source files; the exporter
does not merge that status or change source JSON. It does not rebuild the website.

## References

Full citations for all six source papers, with DOI links and matching JSON files,
are listed in the [main README references](../README.md#references).
