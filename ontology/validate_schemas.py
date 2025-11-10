from loader import load_ontology
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional
import json, glob, pathlib, csv

# -----------------------------
# Docsets & entity mapping
# -----------------------------
DOCSETS = {
    "invoices": "ground_truth/invoices/*.json",
    "intakes":  "ground_truth/intakes/*.json",
    "consents": "ground_truth/consents/*.json",
}

DOC_ENTITY = {
    "invoices": ["Patient", "Encounter", "Claim"],
    "intakes":  ["Patient", "Encounter"],
    "consents": ["Patient", "Encounter", "Consent"],
}

# -----------------------------
# Type mapping
# -----------------------------
TYPE_MAP = {
    "string": str,
    "date": str,
    "decimal": float,
    "integer": int,
    "boolean": bool,
    "array": list,
}

# -----------------------------
# Build Pydantic model dynamically
# -----------------------------
def make_pyd_model(name: str, fields: Dict[str, Any], ont: Any, created_models: Dict[str, BaseModel] = None):
    """Recursively creates a Pydantic model for the entity."""
    created_models = created_models or {}

    annotations = {}
    defaults = {}

    for fname, spec in fields.items():
        py_type = TYPE_MAP[spec.type]

        if spec.type == "array":
            # If items are another entity, recursively create model
            if spec.items in ont.entities:
                nested_model = created_models.get(spec.items) or make_pyd_model(spec.items, ont.entities[spec.items].fields, ont, created_models)
                created_models[spec.items] = nested_model
                py_type = List[nested_model]
            else:
                item_type = TYPE_MAP.get(spec.items or "string", str)
                py_type = List[item_type]

            default = [] if not spec.required else ...
        else:
            default = ... if spec.required else None

        annotations[fname] = py_type
        defaults[fname] = default

    model = type(name, (BaseModel,), {})
    for k in annotations:
        setattr(model, k, defaults[k])
        model.__annotations__ = annotations

    created_models[name] = model
    return model

# -----------------------------
# Extract entity payloads from JSON doc
# -----------------------------
def extract_entity_payloads(doc_json: Dict[str, Any], entity_name: str, ont: Any) -> Dict[str, Any]:
    entity_spec = ont.entities[entity_name]
    payload = {}

    for field_name, field_spec in entity_spec.fields.items():
        if field_name not in doc_json:
            payload[field_name] = [] if field_spec.type == "array" else None
            continue

        value = doc_json[field_name]

        # Handle nested arrays of sub-entities
        if field_spec.type == "array" and field_spec.items in ont.entities:
            nested_entity_name = field_spec.items
            payload[field_name] = [extract_entity_payloads(item, nested_entity_name, ont) for item in value]
        else:
            payload[field_name] = value

    return payload

# -----------------------------
# Main validation routine
# -----------------------------
if __name__ == "__main__":
    ont = load_ontology()
    created_models = {}
    Models = {name: make_pyd_model(name, ent.fields, ont, created_models) for name, ent in ont.entities.items()}

    pathlib.Path("output/reports").mkdir(parents=True, exist_ok=True)
    rows = []

    for set_name, pattern in DOCSETS.items():
        entities = DOC_ENTITY[set_name]
        for path in glob.glob(pattern):
            with open(path) as f:
                data = json.load(f)

            result = {"docset": set_name, "file": path, "ok": True, "errors": []}

            for ent in entities:
                payload = extract_entity_payloads(data, ent, ont)
                try:
                    Models[ent](**payload)
                except ValidationError as e:
                    result["ok"] = False
                    result["errors"].append(f"{ent}: {e.errors()}")

            rows.append(result)

    # Write CSV summary
    with open("output/reports/validation_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["docset", "file", "ok", "errors"])
        writer.writeheader()
        for r in rows:
            writer.writerow({**r, "errors": "; ".join(r["errors"])})

    print("✅ Wrote output/reports/validation_summary.csv")
