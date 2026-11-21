#!/usr/bin/env python3
import json, pathlib, shutil, sys
from jsonschema import Draft202012Validator
from pages import record_page, list_page, collection_page, institutions_page
from rules import check

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, OUT = ROOT/"data"/"records", ROOT/"records"
INST = ROOT/"data"/"institutions"
SCHEMA = json.loads((ROOT/"schema"/"record.schema.json").read_text())
NAMES = json.loads((ROOT/"data"/"collections.json").read_text())
V = Draft202012Validator(SCHEMA)

def main():
    if not DATA.exists():
        sys.exit("no data/records")
    errors, notes, records, seen = [], [], [], {}
    for path in sorted(DATA.rglob("*.json")):
        r = json.loads(path.read_text())
        for e in V.iter_errors(r):
            errors.append(f"{path}: {e.json_path} {e.message}")
        errs, nts = check(r, path)
        errors += errs
        notes += nts
        key = r.get("duplicate_match_key")
        if key:
            if key in seen:
                errors.append(f"{path}: duplicate key {key}, already at {seen[key]}")
            seen[key] = path
        r["_type"] = path.parent.parent.name
        r["_collection"] = path.parent.name
        r["_slug"] = path.stem
        r["_href"] = f'{r["_type"]}/{r["_collection"]}/{r["_slug"]}.html'
        records.append(r)
    for n in notes:
        print(f"note: {n}")
    if errors:
        sys.exit("\n".join(errors))

    if (OUT/"collection").exists():
        shutil.rmtree(OUT/"collection")

    colls = {}
    for r in records:
        name = NAMES.get(r["_collection"], r["_collection"].replace("-", " ").title())
        target = OUT/r["_type"]/r["_collection"]/(r["_slug"] + ".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(record_page(r, name))
        colls.setdefault((name, r["_collection"]), []).append(r)

    (OUT/"collection").mkdir(parents=True, exist_ok=True)
    for (name, slug), items in colls.items():
        items.sort(key=lambda x: x["title"].lower())
        (OUT/"collection"/(slug + ".html")).write_text(collection_page(name, slug, items))

    groups = [(n, s, i) for (n, s), i in sorted(colls.items())]
    (OUT/"index.html").write_text(list_page("Records", 1, "Grouped by collection. Every entry names its source or is flagged unsourced.", groups))

    if INST.exists():
        insts = [json.loads(p.read_text()) for p in sorted(INST.glob("*.json"))]
        counts = {}
        for r in records:
            n = r.get("external_id", {}).get("institution")
            if n:
                counts[n] = counts.get(n, 0) + 1
        (ROOT/"institutions.html").write_text(institutions_page(insts, counts))

    print(f"{len(records)} records")

if __name__ == "__main__":
    main()
