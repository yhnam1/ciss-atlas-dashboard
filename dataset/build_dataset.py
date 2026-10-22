#!/usr/bin/env python3
"""Build a draft demonstration dataset from existing CISS v0.4/v0.5 records.
Standard library only. No AI calls, downloads, or paid services.
This exports a common table; it does not migrate records to a new CISS schema.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def val(x):
    return x.get('value') if isinstance(x, dict) else x


def unit(x):
    return x.get('unit') if isinstance(x, dict) else None


def numeric(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def pack(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            # Keep imported text from being interpreted as spreadsheet formulas.
            w.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v)
                        for k, v in row.items()})


def build():
    rows, papers, combined, checks = [], [], [], []
    seen_papers, seen_rows = set(), set()
    for path in sorted((ROOT / 'records').glob('*.json')):
        raw = path.read_bytes()
        d = json.loads(raw)
        p = d['paper']
        pid = p['paper_id']
        if pid in seen_papers:
            raise ValueError('Duplicate paper_id: ' + pid)
        seen_papers.add(pid)
        sm = {s['sample_id']: s for s in d['samples']}
        su = {s['setup_id']: s for s in d['setups']}
        if len(sm) != len(d['samples']) or len(su) != len(d['setups']):
            raise ValueError('Duplicate sample/setup ID: ' + pid)
        combined.append(d)
        start = len(rows)
        for m in d['measurements']:
            mid = m['measurement_id']
            uid = pid + '::' + mid
            if uid in seen_rows:
                raise ValueError('Duplicate measurement: ' + uid)
            seen_rows.add(uid)
            s, setup = sm[m['sample_id']], su[m['setup_id']]
            mol = s.get('molecule') or {}
            sub = s.get('substrate') or {}
            assembly = s.get('assembly') or {}
            obs = setup.get('observable_definition') or {}
            exc = setup.get('excitation') or {}
            env = setup.get('environment') or {}
            result = m['result']
            source = result.get('source') or {}
            method = setup.get('technique')
            is_spin = method == 'photoemission_mott'
            kind = m.get('record_kind') or 'unspecified_in_original'
            selection = m.get('selection_rule') or 'unspecified_in_original'
            notes = []
            # Explicit export annotations from the earlier source review. Raw records stay intact.
            if pid == 'moellers_2021_dsPNA' and mid in ('M_Au111_cw_check', 'M_Au111_ccw_check'):
                kind = 'calibration_acceptance_criterion'
                notes.append('Reclassified by prior source review; this is not an observed result.')
            if pid == 'moellers_2021_dsPNA' and '_pos1_' in mid:
                selection = 'selected_highest_per_sample'
                notes.append('Figure 5 selection rule recorded in original result.note.')
            if not result.get('qualifier'):
                notes.append('Legacy qualifier not structured; inspect result_note for approximation or bounds.')
            if pid == 'goehler_2011_dsDNA':
                notes.append('Original record flags a sign-convention discrepancy; see raw discrepancies.')
            if d['schema_version'] == '0.4.0':
                notes.append('Legacy geometry provenance has not been corrected by this export.')
            temperature = (m.get('conditions') or {}).get('temperature') or env.get('temperature') or {}
            scope = ('photoelectron_spin_polarization' if is_spin else
                     'photoelectron_yield' if method == 'photoemission_tof' else 'other_method')
            reasons = []
            if not is_spin:
                reasons.append('different_observable_or_method')
            if kind == 'calibration_acceptance_criterion':
                reasons.append('calibration_criterion')
            if not numeric(result.get('value')):
                reasons.append('no_numeric_value')
            if m.get('duplicate_of'):
                reasons.append('explicit_duplicate')
            if result.get('status') != 'reported':
                reasons.append('not_reported_numeric_result')
            if is_spin and numeric(result.get('value')) and result.get('unit') == '%' and abs(result['value']) > 100:
                raise ValueError('Polarization outside [-100,100]: ' + uid)
            if not source:
                checks.append({'record_id': uid, 'issue': 'missing_result_source'})
                reasons.append('missing_result_source')
            row = dict(
                record_id=uid, paper_id=pid, doi=p.get('doi'), year=p.get('year'),
                title=p.get('title'), paper_url='https://doi.org/' + p.get('doi', ''),
                sample_id=m['sample_id'], sample_role=s.get('role'),
                material_class=mol.get('class'), material_name=mol.get('name'),
                stereo_descriptor=mol.get('stereo_descriptor'),
                helix_handedness=val(mol.get('helix_handedness')),
                substrate=sub.get('material'), substrate_facet=sub.get('facet'),
                substrate_crystallinity=sub.get('crystallinity'),
                layer_thickness=val(assembly.get('layer_thickness')),
                layer_thickness_unit=unit(assembly.get('layer_thickness')),
                molecular_n_units=val((mol.get('geometry') or {}).get('n_units')),
                molecular_n_units_unit=unit((mol.get('geometry') or {}).get('n_units')),
                material_treatment=mol.get('treatment'),
                setup_id=m['setup_id'], method=method, dataset_scope=scope,
                observable_symbol=obs.get('symbol'),
                observable_definition=obs.get('formula'),
                spin_component_at_sample=val(obs.get('spin_component')),
                spin_component_at_detector=(setup.get('detection') or {}).get('component_measured'),
                sign_convention=val(obs.get('sign_convention')),
                light_polarization=m.get('light_polarization'),
                wavelength=val(exc.get('wavelength')), wavelength_unit=unit(exc.get('wavelength')),
                temperature=val(temperature), temperature_unit=unit(temperature),
                result_value=result.get('value'), result_unit=result.get('unit'),
                uncertainty=result.get('uncertainty'), uncertainty_type=result.get('uncertainty_type'),
                qualifier=result.get('qualifier') or 'unspecified_in_original',
                extraction_status=result.get('status'), record_kind=kind, selection_rule=selection,
                measurement_group_id=m.get('measurement_group_id'), spot_id=m.get('spot_id'),
                original_dataset_scope=m.get('dataset_scope'), duplicate_of=m.get('duplicate_of'),
                source_document=source.get('doc'), source_location=source.get('loc'),
                source_pdf_page=source.get('pdf_page'), result_note=result.get('note'),
                review_status='unreviewed_draft',
                included_in_numeric_demo=not reasons, exclusion_reason='; '.join(reasons),
                export_notes=' '.join(notes), original_schema_version=d['schema_version'],
                original_record_file='records/' + path.name,
                source_json_sha256=hashlib.sha256(raw).hexdigest(),
                conditions_json=pack(m.get('conditions') or {}),
                measurement_json=pack(m), setup_json=pack(setup), sample_json=pack(s),
            )
            rows.append(row)
        paper_rows = rows[start:]
        papers.append(dict(paper_id=pid, title=p.get('title'), doi=p.get('doi'), year=p.get('year'),
                           measurement_entries=len(paper_rows),
                           numeric_demo_rows=sum(r['included_in_numeric_demo'] for r in paper_rows),
                           graph_placeholders=sum(r['extraction_status'] == 'to_digitize' for r in paper_rows),
                           review_status='unreviewed_draft',
                           coverage='selected_values_only' if 'pilot' in path.name else 'existing_extraction_not_completeness_audited',
                           original_schema_version=d['schema_version'],
                           original_record_file='records/' + path.name))
    demo = [r for r in rows if r['included_in_numeric_demo']]
    # The compact table is convenient in Excel. Complete nested context stays in all_entries.csv and JSON.
    compact_keys = [k for k in rows[0] if not k.endswith('_json') and k not in ('source_json_sha256',)]
    write_csv(ROOT / 'measurements_demo.csv', [{k:r[k] for k in compact_keys} for r in demo])
    write_csv(ROOT / 'all_entries.csv', rows)
    write_csv(ROOT / 'papers.csv', papers)
    (ROOT / 'dataset.jsonl').write_text('\n'.join(pack(r) for r in rows) + '\n', encoding='utf-8')
    summary = dict(dataset_version='hackathon_export_1', papers=len(papers), total_entries=len(rows),
                   numeric_photoelectron_spin_rows=len(demo),
                   test_sample_numeric_rows=sum(r['sample_role'] == 'test' for r in demo),
                   control_numeric_rows=sum(r['sample_role'] != 'test' for r in demo),
                   graph_placeholders=sum(r['extraction_status'] == 'to_digitize' for r in rows),
                   other_excluded_entries=sum(not r['included_in_numeric_demo'] and r['extraction_status'] != 'to_digitize' for r in rows),
                   review_status='unreviewed_draft', live_api_extraction_performed=False,
                   checks={'unique_keys':True,'sample_setup_links':True,'polarization_bounds':True,
                           'issues':checks}, per_paper=papers)
    (ROOT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('per_paper',)}, indent=2))


if __name__ == '__main__':
    build()
