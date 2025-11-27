# predict.py
#
# Usage:
#   python predict.py --input data/phone.csv --column number
#
# Prints ONE of:
#   PhoneNumber, CompanyName, Country, Date, Other

import argparse
import os
import re

import pandas as pd
from dateutil import parser as date_parser

DATA_DIR = "data"
COUNTRIES_FILE = os.path.join(DATA_DIR, "countries.txt")
LEGAL_FILE = os.path.join(DATA_DIR, "legal.txt")


# --------- helpers shared with parser.py ---------

def load_countries(path: str = COUNTRIES_FILE):
    """Return a set of country names in lowercase."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def load_legal_suffixes(path: str = LEGAL_FILE):
    """Return a list of legal suffix strings in lowercase, longest first."""
    suffixes = []
    if not os.path.exists(path):
        return suffixes
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if not line or line.startswith("#"):
                continue
            suffixes.append(line)
    suffixes.sort(key=len, reverse=True)
    return suffixes


def is_parsable_date(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    try:
        # allow many formats; dayfirst=True for things like 08.02.20
        date_parser.parse(s, dayfirst=True, fuzzy=False)
        return True
    except Exception:
        return False


PHONE_REGEX = re.compile(r"[+()\-.\s\d]{6,}")  # loose pattern for phone-like strings


def looks_like_phone(s: str) -> bool:
    s = str(s).strip()
    if not s:
        return False
    # Strip everything except digits
    digits = re.sub(r"\D", "", s)
    # Phone numbers normally between 7 and 15 digits
    return 7 <= len(digits) <= 15


def looks_like_company(s: str, legal_suffixes) -> bool:
    s = str(s).strip()
    if not s:
        return False
    low = s.lower()

    # If any legal suffix appears, it's almost surely a company
    for suf in legal_suffixes:
        pattern = r"\b" + re.escape(suf) + r"\b"
        if re.search(pattern, low):
            return True

    # Fallback keywords
    keywords = ["ltd", "limited", "inc", "corp", "company", "co.", "gmbh", "bank", "plc"]
    return any(k in low for k in keywords)


# ----- scoring functions (column-level probabilities) -----

def score_phone(values) -> float:
    phoney = sum(1 for v in values if looks_like_phone(v))
    return phoney / max(len(values), 1)


def score_date(values) -> float:
    parsable = sum(1 for v in values if is_parsable_date(v))
    return parsable / max(len(values), 1)


def score_country(values, countries_set) -> float:
    if not countries_set:
        return 0.0

    hits = 0
    total = 0
    for v in values:
        v = (v or "").strip().lower()
        if not v:
            continue
        total += 1
        if v in countries_set:
            hits += 1

    if total == 0:
        return 0.0
    return hits / total


def score_company(values, legal_suffixes) -> float:
    positive = sum(1 for v in values if looks_like_company(v, legal_suffixes))
    return positive / max(len(values), 1)


# --------- main CLI ---------

def main():
    parser = argparse.ArgumentParser(description="Semantic column classifier (rule-based)")
    parser.add_argument("--input", required=True, help="Path to CSV file")
    parser.add_argument("--column", required=True, help="Column name in the CSV")
    args = parser.parse_args()

    # Load CSV
    df = pd.read_csv(args.input)
    if args.column not in df.columns:
        raise SystemExit(f"Column '{args.column}' not found in {args.input}")

    # Convert to list of strings
    values = df[args.column].astype(str).fillna("").tolist()

    # Load resources
    countries = load_countries()
    legal_suffixes = load_legal_suffixes()

    # Compute scores
    scores = {}
    scores["PhoneNumber"] = score_phone(values)
    scores["Date"] = score_date(values)
    scores["Country"] = score_country(values, countries)
    scores["CompanyName"] = score_company(values, legal_suffixes)

    # Simple override: if something is VERY clearly phone or date, force it
    if scores["PhoneNumber"] >= 0.8:
        best_label = "PhoneNumber"
    elif scores["Date"] >= 0.8:
        best_label = "Date"
    elif scores["Country"] >= 0.8:
        best_label = "Country"
    else:
        # pick max of all 4
        best_label = max(scores, key=scores.get)
        # if even the max is tiny, call it Other
        if scores[best_label] < 0.3:
            best_label = "Other"

    print(best_label)


if __name__ == "__main__":
    main()
