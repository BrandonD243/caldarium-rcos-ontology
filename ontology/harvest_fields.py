import json, glob, csv, os

INPUT_GLOBS = [
    "ground_truth/invoices/*.json",
    "ground_truth/intakes/*.json",
    "ground_truth/consents/*.json",
]

rows = []
seen = set()

def flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from flatten(v, key)
        else:
            yield key, v

for pattern in INPUT_GLOBS:
    for path in glob.glob(pattern):
        with open(path, "r") as f:
            data = json.load(f)
        for key, val in flatten(data):
            sig = (key, os.path.basename(path))
            if sig not in seen:
                seen.add(sig)
                rows.append([key, os.path.basename(path), type(val).__name__, str(val)[:80]])

os.makedirs("ontology", exist_ok=True)
with open("ontology/field_catalog.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["field_path", "source_file", "python_type", "sample_value"])
    w.writerows(rows)

print("Wrote ontology/field_catalog.csv")