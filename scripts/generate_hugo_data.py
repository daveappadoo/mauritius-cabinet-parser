#!/usr/bin/env python3
"""
Convert cabinet_decisions.csv to decisions.json for Hugo.
Splits ministries_mentioned into an array for JS filtering.
Output: outputs/decisions.json
"""
import csv
import json
from pathlib import Path

INPUT_CSV = "./outputs/cabinet_decisions.csv"
OUTPUT_JSON = "./outputs/decisions.json"

decisions = []

with open(INPUT_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ministries_raw = row.get('ministries_mentioned', '')
        ministries = [m.strip() for m in ministries_raw.split(';') if m.strip()]

        decisions.append({
            'filename':        row['filename'],
            'date':            row['date'],
            'meeting_type':    row['meeting_type'],
            'total_pages':     int(row['total_pages']),
            'decision_number': row['decision_number'],
            'text':            row['text'],
            'ministries':      ministries,
            'ministry_count':  int(row['ministry_count']),
        })

Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(decisions, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(decisions)} decisions to {OUTPUT_JSON}")

# Print unique ministry list for reference
all_ministries = sorted({m for d in decisions for m in d['ministries']})
print(f"\n{len(all_ministries)} unique ministries found:")
for m in all_ministries:
    print(f"  {m}")
