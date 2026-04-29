import json, re
from collections import Counter

ALLOWED_FIELDS = {
    "Economy", "Ecology", "Agriculture", "Health", "Education",
    "Governance", "Diplomacy", "Social", "Technology", "Legal", "Other"
}

KEYWORD_MAP = {
    "Economy": [
        "economic", "finance", "budget", "trade", "investment", "tax", "revenue",
        "bank", "fiscal", "export", "import", "tariff", "customs", "loan", "grant",
        "debt", "financial", "market", "commerce", "business", "industry", "tourism",
        "port", "logistics", "bunkering", "insurance", "pension", "fund", "gdp",
        "inflation", "subsidy", "privatisation", "privatization", "fdi", "sme",
        "enterprise", "credit", "interest rate", "monetary", "free trade",
    ],
    "Ecology": [
        "environment", "ecology", "climate", "pollution", "biodiversity", "marine",
        "ocean", "reef", "conservation", "wildlife", "forest", "emission", "carbon",
        "sustainable", "green", "waste", "recycling", "lagoon", "coastal", "seabed",
        "ecosystem", "flora", "fauna", "endangered", "deforestation", "erosion",
        "renewable energy", "solar", "wind energy", "hydropower",
    ],
    "Agriculture": [
        "agriculture", "farming", "crop", "livestock", "fisheries", "fishing",
        "sugar", "tea", "plantation", "irrigation", "agro", "food security", "harvest",
        "veterinary", "seeds", "fertilizer", "aquaculture", "horticulture", "agrifood",
        "food production", "agricultural", "cane", "dairy", "poultry", "cattle",
    ],
    "Health": [
        "health", "hospital", "medical", "medicine", "disease", "clinic", "doctor",
        "nurse", "pharmaceutical", "drug", "vaccination", "pandemic", "mental health",
        "healthcare", "patient", "surgery", "dental", "cancer", "diabetes", "hiv",
        "aids", "epidemic", "ambulance", "pharmacy", "nutrition", "sanitation",
        "public health", "ncd", "tobacco", "alcohol abuse",
    ],
    "Education": [
        "education", "school", "university", "student", "teacher", "training",
        "curriculum", "scholarship", "academic", "learning", "research", "college",
        "exam", "literacy", "skill development", "vocational", "pre-primary",
        "primary", "secondary", "higher education", "tvet", "institute",
        "pedagogy", "textbook", "school fees",
    ],
    "Governance": [
        "governance", "public service", "reform", "administration", "cabinet",
        "ministry", "regulation", "policy", "law enforcement", "police", "judiciary",
        "election", "parliament", "constitutional", "transparency", "accountability",
        "audit", "procurement", "civil service", "corruption", "ombudsman",
        "municipality", "district council", "local government", "budget speech",
        "public sector", "parastatal", "state-owned", "national assembly",
    ],
    "Diplomacy": [
        "diplomacy", "diplomatic", "bilateral", "multilateral", "international",
        "treaty", "mou", "memorandum of understanding", "ambassador", "embassy",
        "foreign", "united nations", "commonwealth", "sadc", "african union",
        "summit", "state visit", "cooperation agreement", "chagos", "sovereignty",
        "ticad", "g20", "un", "wto", "imf", "world bank", "heads of state",
        "prime minister.*visit", "visit.*prime minister", "foreign minister",
    ],
    "Social": [
        "social", "welfare", "poverty", "community", "housing", "shelter",
        "disability", "gender", "women", "child", "youth", "elderly", "family",
        "culture", "sport", "arts", "religion", "heritage", "volunteer", "ngo",
        "cso", "inclusion", "equality", "discrimination", "domestic violence",
        "orphan", "refugee", "migration", "diaspora", "affordable housing",
    ],
    "Technology": [
        "technology", "digital", "cyber", "internet", "software", "ict", "ai ",
        "artificial intelligence", "data", "satellite", "space", "innovation",
        "startup", "fintech", "broadband", "telecommunications", "e-government",
        "automation", "robotics", "blockchain", "smart city", "5g", "cloud",
        "digitalisation", "digitalization", "e-health", "e-learning",
    ],
    "Legal": [
        "legislation", " act ", "amendment", "bill ", "court", "justice",
        "criminal", "civil law", "rights", "legal", "compliance", "enforcement",
        "tribunal", "judicial", "attorney", "prosecutor", "penal", "offence",
        "penalty", "sentencing", "magistrate", "supreme court", "privy council",
        "extradition", "intellectual property", "copyright", "patent",
    ],
}

def keyword_classify(text):
    t = text.lower()
    matched = [f for f, kws in KEYWORD_MAP.items() if any(re.search(kw, t) for kw in kws)]
    return matched if matched else ["Other"]

import os

with open("outputs/decisions.json") as f:
    decisions = json.load(f)

# Preserve existing classification so re-runs don't reclassify unchanged decisions
if os.path.exists("outputs/decisions_classified.json"):
    with open("outputs/decisions_classified.json") as f:
        old = {d["filename"]: d.get("fields") for d in json.load(f)}
    for d in decisions:
        if d["filename"] in old and old[d["filename"]] is not None:
            d["fields"] = old[d["filename"]]

for d in decisions:
    if "fields" not in d:
        try:
            d["fields"] = keyword_classify(d["text"])
            d["fields"] = [f for f in d["fields"] if f in ALLOWED_FIELDS] or ["Other"]
        except Exception:
            d["fields"] = ["Other"]

with open("outputs/decisions_classified.json", "w") as f:
    json.dump(decisions, f, indent=2, ensure_ascii=False)

# Summary
field_counts = Counter()
other_decisions = []
for i, d in enumerate(decisions):
    for field in d["fields"]:
        field_counts[field] += 1
    if "Other" in d["fields"]:
        other_decisions.append((i, d["date"], d["decision_number"], d["text"][:120]))

print(f"Total decisions: {len(decisions)}")
print("\n=== Field distribution ===")
for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
    print(f"  {field:<15} {count}")

print(f"\n=== Decisions classified as 'Other' ({len(other_decisions)}) ===")
for idx, date, num, snippet in other_decisions:
    print(f"  [{idx}] {date} #{num}: {snippet.strip()}...")