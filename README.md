# Mauritius Cabinet Parser

A Python pipeline for extracting and analysing decisions from Mauritius Cabinet Meeting PDFs.

All PDFs are sourced from the official Prime Minister's Office website:
**https://pmo.govmu.org/Pages/Cabinet_Decisions/Cabinet_Decisions.aspx**

The dataset covers Cabinet Meeting decisions from **10 November 2024 to 24 April 2026**.

---

## Project Structure

```
mauritius-cabinet-parser/
├── pipeline.py                          # Orchestrates the core pipeline steps
├── requirements.txt
├── pdfs/                                # Cabinet meeting PDFs (input)
├── scripts/
│   ├── extractCabinetDecisions.py       # PDF → CSV extraction
│   ├── generate_hugo_data.py            # CSV → decisions.json
│   └── classify.py                      # Keyword-based field classification
├── outputs/
│   ├── cabinet_decisions.csv            # Raw extracted decisions (tabular)
│   ├── decisions.json                   # All decisions as JSON
│   └── decisions_classified.json        # + keyword classification fields
└── logs/
    ├── pipeline.log                     # Pipeline run log
    └── parse_log_*.log                  # Per-run PDF extraction logs
```

---

## Pipeline

Run `pipeline.py` from the project root. It detects new PDFs and runs each step in sequence:

```bash
python pipeline.py
```

| Step | Script |
|------|--------|
| Extract decisions from PDFs | `scripts/extractCabinetDecisions.py` |
| Generate Hugo JSON | `scripts/generate_hugo_data.py` |
| Classify decisions | `scripts/classify.py` |

The pipeline tracks which PDFs have been processed in `outputs/.processed_pdfs.json` and only runs when new PDFs are detected.

---

## Output Files

### `outputs/decisions.json`
Produced by `generate_hugo_data.py`. Each decision has:
- `filename`, `date`, `decision_number`, `total_pages`, `text`

### `outputs/decisions_classified.json`
Produced by `classify.py`. Adds:
- `fields` — list of topic categories (e.g. `["Economy", "Diplomacy"]`)

Available categories: `Economy`, `Ecology`, `Agriculture`, `Health`, `Education`, `Governance`, `Diplomacy`, `Social`, `Technology`, `Legal`, `Other`

---

## Installation

```bash
git clone https://github.com/daveappadoo/mauritius-cabinet-parser.git
cd mauritius-cabinet-parser
pip install -r requirements.txt
```

---

## Data Disclaimer

This tool processes publicly available documents from the Mauritius government website.
The parser is provided as-is for research, analysis, and transparency purposes.
**Verify important information against the original PDF documents.**

The government documents themselves remain under the terms specified by the Government of Mauritius.
