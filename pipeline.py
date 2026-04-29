#!/usr/bin/env python3
"""
Pipeline: detect new PDFs → extract → generate JSON → classify.
Logs to logs/pipeline.log.
"""
import json
import logging
import subprocess
import sys
from pathlib import Path

PDF_DIR    = Path("./pdfs")
STATE_FILE = Path("./outputs/.processed_pdfs.json")
LOG_FILE   = Path("./logs/pipeline.log")
PYTHON     = sys.executable

STEPS = [
    ("Extract decisions from PDFs", "scripts/extractCabinetDecisions.py"),
    ("Generate Hugo JSON",          "scripts/generate_hugo_data.py"),
    ("Classify decisions",          "scripts/classify.py"),
]


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)


def current_pdfs() -> set[str]:
    return {p.name for p in PDF_DIR.glob("*.pdf")}


def load_state() -> set[str]:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_state(pdfs: set[str]):
    STATE_FILE.write_text(json.dumps(sorted(pdfs), indent=2))


def run_step(label: str, script: str) -> bool:
    logging.info(f"── {label}")
    proc = subprocess.Popen(
        [PYTHON, "-u", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    for line in (proc.stdout or []):
        logging.info(f"    {line.rstrip()}")
    proc.wait()
    if proc.returncode != 0:
        logging.error(f"    FAILED (exit {proc.returncode})")
        return False
    logging.info(f"    OK")
    return True


def main():
    setup_logging()
    logging.info("=" * 60)
    logging.info(f"Pipeline started")

    known = load_state()
    found = current_pdfs()
    new   = found - known

    if not new:
        logging.info(f"No new PDFs found ({len(found)} already processed). Exiting.")
        return

    logging.info(f"New PDFs detected ({len(new)}):")
    for name in sorted(new):
        logging.info(f"    + {name}")

    for label, script in STEPS:
        ok = run_step(label, script)
        if not ok:
            logging.error("Pipeline aborted.")
            sys.exit(1)

    save_state(found)
    logging.info(f"Pipeline complete. State updated ({len(found)} PDFs tracked).")


if __name__ == "__main__":
    main()
