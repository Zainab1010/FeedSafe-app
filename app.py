"""
FeedSafe backend — Stage 4
===========================
A small Flask server that:
  1. Loads the real medications.json database into memory.
  2. Exposes it over two simple API endpoints the frontend calls.
  3. Serves index.html itself, so "python app.py" runs the whole app —
     one command, one URL, no separate frontend server needed.

Run with:
    pip install flask --break-system-packages
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

from flask import Flask, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

# The database file lives next to this script.
DB_PATH = os.path.join(os.path.dirname(__file__), "medications.json")


def load_medication_database():
    """
    Opens medications.json, reads it, and parses it into a Python list
    of dictionaries — one dictionary per medication.
    """
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_medication(name, database):
    """
    Looks up a medication by generic name OR any of its brand names,
    case-insensitively and with extra whitespace stripped. Returns the
    matching entry, or None if nothing matches.
    """
    query = name.strip().lower()

    for entry in database:
        if entry["generic_name"].lower() == query:
            return entry
        for brand in entry.get("brand_names", []):
            if brand.lower() == query:
                return entry

    return None


# Load the database ONCE when the server starts, not on every request.
medication_database = load_medication_database()


@app.route("/api/medications")
def api_list_medications():
    """Returns every medication in the database — used to build the quick-choice pills."""
    return jsonify(medication_database)


@app.route("/api/search/<name>")
def api_search(name):
    """Returns one medication's full record, or a clear 'not found' payload."""
    result = search_medication(name, medication_database)
    if result:
        return jsonify({"found": True, "medication": result})
    return jsonify({"found": False, "medication": None})


@app.route("/")
def serve_index():
    """Serves the frontend file, so one command runs the entire app."""
    return send_from_directory(os.path.dirname(__file__), "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
