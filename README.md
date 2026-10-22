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
The dashboard HTML contains its own display code and embedded dataset. This curated
package does not include the private dashboard build system or source PDFs.

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
The public pipeline package is a curated snapshot and must be updated separately.
