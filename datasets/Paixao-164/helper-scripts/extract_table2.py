#!/usr/bin/env python3
"""
Extract Table 2 (164 drugs) from Paixão et al. (2012) Int. J. Pharm. 429:84-98.

Usage:
    python extract_table2.py paper.pdf table2.csv

Requires poppler's `pdftotext` (conda install conda-forge::poppler)
and pandas.  Table 2 sits on journal pages 87-89 (PDF pages 4-6 of the reprint).
"""
import re
import subprocess
import sys

import pandas as pd

PDF = sys.argv[1] if len(sys.argv) > 1 else "Paixão et al. - 2012 - Prediction of the human oral bioavailability by us.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "table2.csv"
FIRST_PAGE, LAST_PAGE = 4, 6          # PDF page numbers holding Table 2

# --- 1. get layout-preserving text ------------------------------------------
text = subprocess.run(
    ["pdftotext", "-f", str(FIRST_PAGE), "-l", str(LAST_PAGE), "-layout", PDF, "-"],
    capture_output=True, text=True, check=True,
).stdout

# Typographic ligatures / unicode minus show up in drug names (Cefixime, Ciprofloxacin...)
text = (text.replace("\ufb01", "fi").replace("\ufb02", "fl")
            .replace("\u2212", "-"))

# --- 2. parse rows ----------------------------------------------------------
NUM = r"(\d+\.\d+)"
ROW = re.compile(
    r"^\s*(?P<drug>[A-Za-z][A-Za-z0-9\- ]*?)\s{2,}"
    + r"\s+".join([
        rf"(?P<Foral>{NUM})", rf"(?P<frenal>{NUM})", rf"(?P<fp>{NUM})",
        rf"(?P<Clplasma>{NUM})", rf"(?P<Rb>{NUM})",
        r"(?P<drug_class>[ABNZ])",
        rf"(?P<ClH>{NUM})", rf"(?P<Fabs>{NUM})", rf"(?P<Fmet>{NUM})",
    ])
    + r"\s+(?P<refs>(?:\([A-Z]{1,2}\)\s*)+)\s*$"
)

rows = []
for line in text.splitlines():
    m = ROW.match(line)
    if m:
        d = m.groupdict()
        d["refs"] = " ".join(re.findall(r"\(([A-Z]{1,2})\)", d["refs"]))
        rows.append(d)

# Regex has nested groups (NUM) -> keep only the named ones
cols = ["drug", "Foral", "frenal", "fp", "Clplasma", "Rb",
        "drug_class", "ClH", "Fabs", "Fmet", "refs"]
df = pd.DataFrame(rows)[cols]
num_cols = ["Foral", "frenal", "fp", "Clplasma", "Rb", "ClH", "Fabs", "Fmet"]
df[num_cols] = df[num_cols].astype(float)
df = df.rename(columns={"Clplasma": "Clplasma_ml_min_kg", "ClH": "ClH_ml_min_kg"})

# --- 3. sanity checks -------------------------------------------------------
print(f"Parsed {len(df)} rows (paper states 164)")
assert len(df) == 164, "Row count mismatch - inspect the text for unparsed lines"
assert df["drug"].is_unique, "Duplicate drug names"
assert df["drug_class"].isin(list("ABNZ")).all()
assert df[["Foral", "frenal", "fp", "Fabs", "Fmet"]].apply(lambda s: s.between(0, 1)).all().all()

df.to_csv(OUT, index=False)
print(f"Wrote {OUT}")
