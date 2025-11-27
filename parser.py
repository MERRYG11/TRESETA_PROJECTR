# parser.py
#
# Usage:
#   python parser.py --input data/test.csv
#
# Reads the CSV, finds the best PhoneNumber or CompanyName column
# using the same scoring logic as predict.py, parses it, and writes output.csv.

import argparse
import os
import re

import pandas as pd

from predict import (
    load_countries,
    load_legal_suffixes,
    score_phone,
    score_company,
)

DATA_DIR = "data"
LEGAL_FILE = os.path.join(DATA_DIR, "legal.txt")

# ------------- company name parsing -------------

def parse_company_name(raw: str, suffixes):
    s = str(raw).strip()
    if not s:
        return "", ""

    low = s.lower()

    for suf in suffixes:
        pattern = r"\b" + re.escape(suf) + r"\b\.?"
        m = re.search(pattern, low)
        if m:
            start = m.start()
            name_part = s[:start].strip(" ,.-")
            legal_part = s[start:].strip(" ,.-")
            return name_part, legal_part

    # No known suffix found
    return s, ""


# ------------- phone parsing helpers -------------

# Very small mapping for demo; can be extended easily
DIAL_CODE_TO_COUNTRY = {
    "1": "US",
    "44": "UK",
    "91": "India",
}


def parse_phone_number(raw: str):
    """
    Split into (Country, Number) using dial code if present.
    If no or unknown country code, country is empty string and
    Number is just all digits.
    """
    s = str(raw).strip()
    digits = re.sub(r"\D", "", s)
    if not digits:
        return "", ""

    # Default: no country detected
    country = ""
    subscriber_number = digits

    if s.startswith("+"):
        # Try dial codes of length 3,2,1
        for length in (3, 2, 1):
            if len(digits) >= length:
                code = digits[:length]
                if code in DIAL_CODE_TO_COUNTRY:
                    country = DIAL_CODE_TO_COUNTRY[code]
                    subscriber_number = digits[length:]
                    break

    return country, subscriber_number


# ------------- main logic -------------


def main():
    ap = argparse.ArgumentParser(description="Parse phone/company columns and write output.csv")
    ap.add_argument("--input", required=True, help="Input CSV file path")
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    if df.empty:
        raise SystemExit("Input CSV is empty.")

    # Load resources
    countries = load_countries()
    legal_suffixes = load_legal_suffixes()

    # Score each column as possible phone or company (rule-based)
    candidates = []
    for col in df.columns:
        values = df[col].astype(str).fillna("").tolist()
        phone_score = score_phone(values)
        company_score = score_company(values, legal_suffixes)

        candidates.append((col, "PhoneNumber", phone_score))
        candidates.append((col, "CompanyName", company_score))

    # Choose best candidate overall
    best_col, best_type, best_score = max(candidates, key=lambda x: x[2])

    out_df = df.copy()

    if best_type == "PhoneNumber" and best_score > 0:
        # Parse phone column
        country_col = []
        number_col = []
        for v in out_df[best_col]:
            c, n = parse_phone_number(v)
            country_col.append(c)
            number_col.append(n)

        # Names required by the problem statement
        out_df["Country"] = country_col
        out_df["Number"] = number_col

    elif best_type == "CompanyName" and best_score > 0:
        # Parse company column
        name_col = []
        legal_col = []
        for v in out_df[best_col]:
            name, legal = parse_company_name(v, legal_suffixes)
            name_col.append(name)
            legal_col.append(legal)

        out_df["Name"] = name_col
        out_df["Legal"] = legal_col

    # Write output.csv in project root
    out_path = "output.csv"
    out_df.to_csv(out_path, index=False)

    print(f"Input file: {args.input}")
    print(f"Best parsed column: {best_col} (type={best_type}, score={best_score:.2f})")
    print(f"Wrote parsed data to {out_path}")


if __name__ == "__main__":
    main()
