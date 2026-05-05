#!/usr/bin/env python3
import json
import time
import sys
import os

# Ensure workspace root is on sys.path so we can import backend/ frontend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text


def main():
    try:
        import backend.db as db
        import backend.main as mainmod
    except Exception as e:
        print('Error importing backend modules:', e, file=sys.stderr)
        sys.exit(1)

    if not getattr(db, 'is_db_enabled', lambda: False)():
        print('Database is not enabled (ENGINE missing). Aborting.')
        return

    with db.ENGINE.begin() as conn:
        rows = conn.execute(text("SELECT id::text AS id, filters_json FROM analysis_runs ORDER BY created_at DESC"))
        fetched = rows.mappings().all()

    print(f'Found {len(fetched)} analysis_runs')

    processed = 0
    for r in fetched:
        analysis_run_id = r.get('id')
        filters_json = r.get('filters_json')
        try:
            if isinstance(filters_json, str):
                filters = json.loads(filters_json) if filters_json else {}
            elif filters_json is None:
                filters = {}
            else:
                filters = filters_json
        except Exception:
            filters = {}

        print('\n---')
        print('Processing analysis_run:', analysis_run_id)
        print('filters:', filters)

        try:
            fp = mainmod.FiltersPayload(**(filters or {}))
            computed = mainmod._compute_analysis_bundle(fp)
        except Exception as e:
            print('compute bundle failed, falling back to empty FiltersPayload:', e)
            computed = mainmod._compute_analysis_bundle(mainmod.FiltersPayload())

        evidence = {
            'kpis': computed.get('kpis', {}),
            'sales_trend': computed.get('sales_trend', []),
            'category_sales': computed.get('category_sales', []),
            'region_sales': computed.get('region_sales', []),
            'forecast': computed.get('forecast', []),
            'rfm': computed.get('rfm', {}),
            'what_if': computed.get('what_if', {}),
        }

        try:
            widgets = mainmod._default_widgets(evidence, filters=filters)
        except TypeError:
            widgets = mainmod._default_widgets(evidence)
        except Exception as e:
            print('Error generating widgets for', analysis_run_id, e)
            widgets = mainmod._default_widgets(evidence)

        # delete old widgets
        try:
            with db.ENGINE.begin() as conn:
                conn.execute(text("DELETE FROM analysis_widgets WHERE analysis_run_id = CAST(:id AS UUID)"), {"id": analysis_run_id})
        except Exception as e:
            print('Failed to delete old widgets for', analysis_run_id, e)

        # save new widgets
        try:
            db.save_widgets(analysis_run_id, mainmod._coerce_for_json(widgets))
            print('Saved', len(widgets), 'widgets for', analysis_run_id)
            processed += 1
        except Exception as e:
            print('Failed to save widgets for', analysis_run_id, e)

    print('\nRegeneration complete. Processed', processed, 'runs')

    # quick verification: call API endpoints for a few sample chart requests
    try:
        import requests
        base = 'http://localhost:8000/api/ai/insights'

        def post(payload):
            try:
                r = requests.post(base, json=payload, timeout=30)
                print('\nREQUEST:', json.dumps(payload, ensure_ascii=False))
                print('STATUS:', r.status_code)
                try:
                    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
                except Exception:
                    print(r.text)
            except Exception as e:
                print('Request failed:', e)

        # no filters
        p0 = {"chartId": "daily-sales-trend", "chartType": "line", "detailLevel": "short", "locale": "vi"}
        # specific filter set
        p1 = {"chartId": "daily-sales-trend", "chartType": "line", "filters": {"category": ["Furniture"], "region": ["South"]}, "timeRange": {"from": "2014-01-01", "to": "2014-12-31"}, "detailLevel": "short", "locale": "vi"}
        p2 = {"chartId": "daily-sales-trend", "chartType": "line", "filters": {"category": ["Technology"], "region": ["West"], "start_date": "2017-01-01", "end_date": "2017-12-31"}, "detailLevel": "short", "locale": "vi"}

        post(p0)
        time.sleep(0.5)
        post(p1)
        time.sleep(0.5)
        post(p2)
    except Exception as e:
        print('Verification requests failed or skipped:', e)


if __name__ == '__main__':
    main()
