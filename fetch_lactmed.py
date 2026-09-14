"""
FeedSafe — Stage 4: Fetching REAL LactMed data from the National Library
of Medicine (NLM)
==========================================================================

READ THIS FIRST — a reality check that will save you a lot of confusion:

LactMed does NOT publish a REST API that hands back a clean JSON object
with a "risk_level" field. It's a set of text monographs hosted on NCBI
Bookshelf. What NLM *does* provide, for free, with no API key required
for light use, is "E-utilities" — a real, public API that lets a script:

  1. Search NCBI's "books" database for a drug's LactMed record  (esearch)
  2. Pull that record's actual monograph text                     (efetch)

That's what this script does. It fetches the CURRENT, REAL text NLM
publishes for each drug — nothing invented.

It deliberately does NOT try to auto-generate a "risk_level" or a short
"lactmed_summary", because turning a clinical monograph into a risk tier
is a judgment call that belongs to a human (ideally a pharmacist or
lactation consultant) reading the actual text — not something a script
(or an AI) should decide silently. This script's output is the raw
material for that review step, saved in a clean JSON structure so it's
easy to hand off.

Requires: pip install requests --break-system-packages
"""

import requests
import json
import time

# NLM's public E-utilities base URL.
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_lactmed_record(drug_name):
    """
    Looks up ONE drug's LactMed monograph on NCBI Bookshelf and returns
    the real text NLM publishes for it, plus a link back to the source
    so a reviewer can double-check it.
    """
    # --- Step 1: search the "books" database for this drug's LactMed entry ---
    search_url = f"{EUTILS_BASE}/esearch.fcgi"
    search_params = {
        "db": "books",
        "term": f"{drug_name}[Title] AND lactmed[Filter]",
        "retmode": "json",
    }
    search_response = requests.get(search_url, params=search_params, timeout=10)
    search_data = search_response.json()

    id_list = search_data.get("esearchresult", {}).get("idlist", [])

    # If NLM has no LactMed record under this name, say so honestly —
    # never guess or fill in a fake result.
    if not id_list:
        return {
            "generic_name": drug_name,
            "found": False,
            "raw_monograph_text": None,
            "source_url": None,
        }

    book_id = id_list[0]

    # --- Step 2: fetch the actual monograph text for that record ---
    fetch_url = f"{EUTILS_BASE}/efetch.fcgi"
    fetch_params = {
        "db": "books",
        "id": book_id,
        "rettype": "full",
        "retmode": "text",
    }
    fetch_response = requests.get(fetch_url, params=fetch_params, timeout=10)

    return {
        "generic_name": drug_name,
        "found": True,
        "raw_monograph_text": fetch_response.text.strip(),
        "source_url": f"https://www.ncbi.nlm.nih.gov/books/{book_id}/",
    }


def build_medication_file(drug_list, output_path="medications_raw.json"):
    """
    Loops over a list of drug names, fetches each one's real LactMed
    text, and writes it all to a pretty-printed JSON file — the input
    a human reviewer uses to fill in risk_level and lactmed_summary.
    """
    results = []
    for drug_name in drug_list:
        print(f"Fetching: {drug_name} ...")
        record = fetch_lactmed_record(drug_name)
        results.append(record)
        time.sleep(0.4)  # be polite to NLM's free public servers

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} records to {output_path}")
    print("Next step: a clinician/pharmacist reviews each raw_monograph_text")
    print("and fills in risk_level + lactmed_summary using the schema in")
    print("medications.json — do not auto-generate those two fields.")


if __name__ == "__main__":
    test_drugs = ["Ibuprofen", "Amoxicillin"]
    build_medication_file(test_drugs)
