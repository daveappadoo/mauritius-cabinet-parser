#!/usr/bin/env python3
"""
PDF parser for Mauritius Cabinet Meeting decisions
Extracts text using PyMuPDF
Detects ministries mentioned in decisions
"""
import pymupdf
import re
import csv
import logging
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser


# List of all 48 ministries and departments
MINISTRIES = [
    "Prime Minister's Office",
    "Ministry of Defence, Home Affairs and External Communications; Ministry for Rodrigues, Outer Islands & Territorial Integrity",
    "Ministry Of Energy and Public Utilities",
    "Ministry of Education, Tertiary Education, Science and Technology",
    "Ministry of Local Government, Disaster and Risk Management",
    "Ministry of Finance, Economic Planning and Development",
    "Ministry of Foreign Affairs, Regional Integration and International Trade",
    "Ministry of Housing and Land Use Planning",
    "Ministry of Industrial Development, SMEs and Cooperatives",
    "Ministry of Environment, Solid Waste Management and Climate Change",
    "Ministry of Financial Services and Good Governance",
    "Ministry of Tourism",
    "Ministry of Justice, Human Rights & Institutional Reforms",
    "National Human Rights Commission",
    "Ministry of Agro Industry and Food Security",
    "Ministry of Commerce and Consumer Protection",
    "Ministry of Youth Empowerment, Sports and Recreation",
    "Ministry of Information Technology, Communication and Innovation",
    "Ministry of Labour, Human Resource Development and Training",
    "Ministry of Health and Wellness",
    "Ministry of Blue Economy, Marine Resources, Fisheries and Shipping",
    "Ministry of Gender Equality and Family Welfare",
    "Ministry of Arts and Cultural Heritage",
    "Ministry of Public Service, Administrative and Institutional Reforms",
    "Ministry of National Infrastructure and Community Development",
    "Ministry of Social Security and National Solidarity",
    "Ministry of Social Integration and Economic Empowerment",
    "Ministry of Land Transport and Light Rail",
    "Police Department",
    "Mauritius Public Service",
    "National Land Transport Authority",
    "Office for Ombudsperson for Financial Services",
    "Procurement Policy Office",
    "Local Government Service Commission",
    "Public Service Commission",
    "Mauritius National Assembly",
    "Statistics Mauritius",
    "Office of the Electoral Commissioner",
    "Civil Status Division",
    "National Archives Department",
    "Corporate & Business Registration Department",
    "Department of Civil Aviation",
    "Ambassade de France à Maurice",
    "National Arts Fund",
    "Irrigation Authority",
    "Office of the Ombudsman",
]


def find_ministries_in_text(text):
    """
    Find all ministries mentioned in the text
    Returns: tuple of (list of ministries found, count)
    """
    if not text:
        return [], 0
    
    text_normalized = text.lower()
    found_ministries = []
    
    for ministry in MINISTRIES:
        # Create case-insensitive pattern
        ministry_pattern = re.escape(ministry.lower())
        
        if re.search(ministry_pattern, text_normalized):
            found_ministries.append(ministry)
    
    # Remove duplicates while preserving order
    unique_ministries = []
    for ministry in found_ministries:
        if ministry not in unique_ministries:
            unique_ministries.append(ministry)
    
    return unique_ministries, len(unique_ministries)


def extract_date_from_filename(filename):
    """Extract date from PDF filename"""
    patterns = [
        r'(\d{1,2}[_\s]+\w+[_\s]+\d{4})',  # 31 January 2025
        r'(\d{1,2}\.\d{2}\.\d{2,4})',       # 31.01.2025 or 13.12.24
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',   # 31-01-2025
        r'(\w+[_\s]+\d{1,2}[_\s]+\d{4})',   # January 31 2025
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1).replace('_', ' ').replace('.', ' ')
                parsed_date = date_parser.parse(date_str, fuzzy=True)
                return parsed_date.strftime("%Y-%m-%d")
            except:
                continue
    return None


def clean_extracted_text(text):
    """Clean raw PyMuPDF text before parsing"""
    # Strip page headers injected between pages (e.g. "Page 2 of 6")
    text = re.sub(r'Page \d+ of \d+\s*', '', text)
    # Normalise curly apostrophes and smart quotes to ASCII equivalents
    text = text.replace('’', "'").replace('‘', "'")
    text = text.replace('“', '"').replace('”', '"')
    # Remove separator lines that are only asterisks
    text = re.sub(r'\n\s*\*+\s*\n', '\n', text)
    return text


def extract_text_pymupdf(pdf_path):
    """Extract text using PyMuPDF (pymupdf)"""
    text = ""
    try:
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n"
        doc.close()
        return clean_extracted_text(text), total_pages
    except Exception as e:
        logging.error(f"PyMuPDF extraction failed: {e}")
        return None, 0


def extract_date_from_text(text):
    """Extract date from PDF header"""
    if not text:
        return None
    header_match = re.search(r'CABINET MEETING\s*[–-]\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if header_match:
        date_str = header_match.group(1).strip()
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=True)
            return parsed_date.strftime("%Y-%m-%d")
        except:
            pass
    return None


def extract_meeting_type(text):
    """Detect whether this is a regular or special cabinet meeting"""
    if not text:
        return 'regular'
    if re.search(r'SPECIAL CABINET MEETING', text, re.IGNORECASE):
        return 'special'
    return 'regular'


def parse_narrative_decisions(text):
    """Fallback parser for unnumbered/special meeting documents.
    Splits on 'Cabinet has' sentence boundaries."""
    if not text:
        return []
    body_match = re.search(r'(Cabinet has.+)', text, re.DOTALL | re.IGNORECASE)
    if not body_match:
        return []
    body = re.sub(r'\*+\s*$', '', body_match.group(1)).strip()
    segments = re.split(r'(?=\bCabinet has\b)', body, flags=re.IGNORECASE)
    decisions = []
    for i, segment in enumerate(segments, 1):
        segment = ' '.join(segment.split()).strip()
        if len(segment) >= 20:
            decisions.append({'number': str(i), 'text': segment})
    return decisions


def parse_decisions(text):
    """Parse individual decisions from text"""
    if not text:
        return []

    decisions = []
    decision_pattern = r'\n(\d{1,3})\.\s+'
    parts = re.split(decision_pattern, text)

    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            decision_num = parts[i]
            decision_text = parts[i + 1]
            decision_text = re.sub(r'\*+', '', decision_text)
            decision_text = decision_text.strip()

            if len(decision_text) < 20:
                continue

            decision_text = ' '.join(decision_text.split())
            decisions.append({
                'number': decision_num,
                'text': decision_text
            })

    return decisions


def setup_logging():
    """Set up logging configuration"""
    Path("./logs").mkdir(parents=True, exist_ok=True)

    log_filename = f"./logs/parse_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_filename


def main():
    pdf_dir = Path("./pdfs")
    output_file = "./outputs/cabinet_decisions.csv"
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    log_filename = setup_logging()
    logging.info(f"Starting PDF parsing process using PyMuPDF")
    logging.info(f"Log file: {log_filename}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    logging.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

    all_decisions = []
    extraction_stats = {
        'files_processed': 0,
        'files_failed': 0
    }

    for pdf_file in pdf_files:
        logging.info(f"\nProcessing: {pdf_file.name}")

        try:
            # Extract using PyMuPDF
            logging.info("  Extracting with PyMuPDF...")
            text, total_pages = extract_text_pymupdf(pdf_file)

            if not text:
                logging.warning(f"  Extraction failed for {pdf_file.name}")
                extraction_stats['files_failed'] += 1
                continue

            # Extract date
            meeting_date = extract_date_from_text(text)
            if not meeting_date:
                meeting_date = extract_date_from_filename(pdf_file.name)
            
            if not meeting_date:
                logging.warning(f"  Could not extract date from {pdf_file.name}, skipping")
                continue

            logging.info(f"  Date: {meeting_date}")

            meeting_type = extract_meeting_type(text)

            # Parse decisions
            decisions = parse_decisions(text)
            if not decisions:
                decisions = parse_narrative_decisions(text)
                if decisions:
                    logging.info(f"  Numbered decisions not found; using narrative fallback")
            logging.info(f"  Extracted {len(decisions)} decisions")

            # Add to results
            for decision in decisions:
                # Find ministries mentioned in this decision
                ministries_found, ministry_count = find_ministries_in_text(decision['text'])

                all_decisions.append({
                    'filename': pdf_file.name,
                    'date': meeting_date,
                    'meeting_type': meeting_type,
                    'total_pages': total_pages,
                    'decision_number': decision['number'],
                    'text': decision['text'],
                    'ministries_mentioned': '; '.join(ministries_found) if ministries_found else '',
                    'ministry_count': ministry_count
                })
                
                if ministries_found:
                    logging.info(f"    Decision {decision['number']}: Found {ministry_count} ministries")

            extraction_stats['files_processed'] += 1

        except Exception as e:
            logging.error(f"  Error processing {pdf_file.name}: {e}", exc_info=True)
            extraction_stats['files_failed'] += 1

    # Write to CSV
    logging.info(f"\nWriting {len(all_decisions)} decisions to {output_file}")

    fieldnames = [
        'filename', 'date', 'meeting_type', 'total_pages', 'decision_number', 'text',
        'ministries_mentioned', 'ministry_count'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_decisions)

    logging.info(f"CSV file created: {output_file}")

    # Print summary
    if all_decisions:
        dates = set(d['date'] for d in all_decisions)
        total_ministry_mentions = sum(d['ministry_count'] for d in all_decisions)
        decisions_with_ministries = sum(1 for d in all_decisions if d['ministry_count'] > 0)
        
        logging.info(f"\n=== Summary ===")
        logging.info(f"Total PDF files found: {len(pdf_files)}")
        logging.info(f"Files processed successfully: {extraction_stats['files_processed']}")
        logging.info(f"Files failed: {extraction_stats['files_failed']}")
        logging.info(f"Total decisions extracted: {len(all_decisions)}")
        logging.info(f"Unique meeting dates: {len(dates)}")
        logging.info(f"Date range: {min(dates)} to {max(dates)}")
        logging.info(f"\n=== Ministry Detection ===")
        logging.info(f"Decisions with ministries mentioned: {decisions_with_ministries}")
        logging.info(f"Total ministry mentions: {total_ministry_mentions}")
        logging.info(f"Average ministries per decision: {total_ministry_mentions/len(all_decisions):.2f}")
    
    logging.info(f"\nLog file saved: {log_filename}")


if __name__ == "__main__":
    main()