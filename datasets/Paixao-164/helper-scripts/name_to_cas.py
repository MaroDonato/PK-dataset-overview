#!/usr/bin/env python3
"""
Add CAS numbers to table2.csv by resolving drug names online.

Usage:
    pip install requests pandas
    python name_to_cas.py table2.csv ../table2_with_cas.csv

Strategy (per drug):
  1. PubChem PUG-REST: name -> CID -> synonym list -> keep strings shaped like a CAS RN
     (NNNNNNN-NN-N) whose check digit is valid.
  2. Anything PubChem cannot resolve is flagged for manual lookup.

Output columns added:
    name_used   name actually sent to the services (after corrections)
    cid         PubChem compound ID of the first name match
    cas         best-guess CAS RN (first valid one in PubChem's synonym order)
    cas_all     all valid CAS RNs found (';'-separated) - check when there is more than one
    cas_source  pubchem | NOT_FOUND
"""
import re
import sys
import time

import pandas as pd
import requests

IN = sys.argv[1] if len(sys.argv) > 1 else "table2.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../table2_with_cas.csv"

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "table2-cas-lookup/1.0 (research use)"

# Names in the paper that need fixing before lookup (typos / non-INN spellings).
NAME_FIXES = {
    "Amiodarona": "Amiodarone",          # typo in the paper's Table 2
    "Isosorbide-5-mononitrate": "Isosorbide mononitrate",
    "Glyburide": "Glibenclamide",        # same compound, INN name resolves better
}

CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")


def valid_cas(s: str) -> bool:
    """Format + check-digit validation (weights 1,2,3... from the right, mod 10)."""
    if not CAS_RE.match(s):
        return False
    digits = s.replace("-", "")
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * w for w, d in enumerate(reversed(body), start=1))
    return total % 10 == check


def extract_cas(strings):
    seen, out = set(), []
    for s in strings:
        s = s.strip()
        if s not in seen and valid_cas(s):
            seen.add(s)
            out.append(s)
    return out


def get_json(url, retries=3):
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:          # PubChem: no match
                return None
            if r.status_code in (429, 503):   # throttled -> back off
                time.sleep(2 * (attempt + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return None


def pubchem_lookup(name):
    cids = get_json(f"{PUBCHEM}/name/{requests.utils.quote(name)}/cids/JSON")
    if not cids:
        return None, []
    cid = cids["IdentifierList"]["CID"][0]
    time.sleep(0.25)                          # stay under PubChem's 5 req/s limit
    syn = get_json(f"{PUBCHEM}/cid/{cid}/synonyms/JSON")
    if not syn:
        return cid, []
    names = syn["InformationList"]["Information"][0].get("Synonym", [])
    return cid, extract_cas(names)


def resolve(name):
    cid, cas = pubchem_lookup(name)
    if cas:
        return cid, cas, "pubchem"
    return cid, [], "NOT_FOUND"


if __name__ == "__main__":
    df = pd.read_csv(IN)
    results = []
    for i, drug in enumerate(df["drug"], 1):
        name = NAME_FIXES.get(drug, drug)
        cid, cas, src = resolve(name)
        results.append({
            "name_used": name,
            "cid": cid,
            "cas": cas[0] if cas else "",
            "cas_all": ";".join(cas),
            "cas_source": src,
        })
        print(f"[{i:3d}/{len(df)}] {drug:28s} -> {cas[0] if cas else 'NOT FOUND'}"
              f"{'  (+%d more)' % (len(cas) - 1) if len(cas) > 1 else ''}")
        time.sleep(0.25)

    out = pd.concat([df, pd.DataFrame(results)], axis=1)
    out.to_csv(OUT, index=False)

    n_found = (out["cas_source"] != "NOT_FOUND").sum()
    print(f"\nResolved {n_found}/{len(out)}; wrote {OUT}")
    missing = out.loc[out["cas_source"] == "NOT_FOUND", "drug"].tolist()
    if missing:
        print("Look up manually:", ", ".join(missing))
    multi = out.loc[out["cas_all"].str.count(";") > 0, "drug"].tolist()
    if multi:
        print("Multiple CAS RNs found (verify the 'cas' column):", ", ".join(multi))