from ontology.loader import load_ontology
from pydantic import BaseModel, create_model
from typing import Dict, Any, List, Optional, Type
import json, os

# -----------------------------
# Type mapping
# -----------------------------
TYPE_MAP = {
    "string": str,
    "date": str,
    "decimal": float,
    "integer": int,
    "boolean": bool,
}

# -----------------------------
# Recursive Pydantic model generator
# -----------------------------
def make_pyd_model(name: str, fields: Dict[str, Any], ont: Any, created_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
    """
    Generate a Pydantic model class for the entity, recursively creating sub-models for nested arrays.
    """
    if created_models is None:
        created_models = {}

    if name in created_models:
        return created_models[name]

    annotations = {}
    defaults = {}

    for fname, spec in fields.items():
        # Determine type
        if spec.type == "array":
            if spec.items in ont.entities:
                # Nested entity array -> sub-model
                sub_model = make_pyd_model(spec.items, ont.entities[spec.items].fields, ont, created_models)
                py_type = List[sub_model]
            else:
                # Array of primitives
                item_type = TYPE_MAP.get(spec.items or "string", str)
                py_type = List[item_type]
            default = [] if not spec.required else ...
        else:
            py_type = TYPE_MAP[spec.type]
            default = ... if spec.required else None
            if not spec.required:
                py_type = Optional[py_type]

        annotations[fname] = py_type
        defaults[fname] = default

    Model = create_model(name, **{k: (annotations[k], defaults[k]) for k in annotations})
    created_models[name] = Model
    return Model

# -----------------------------
# Generate Python code string
# -----------------------------
def make_pyd_model_code(name: str, fields: Dict[str, Any], ont: Any, created_models: Dict[str, Type[BaseModel]] = None) -> str:
    """
    Generate Python code for a Pydantic model as a string.
    Handles nested array sub-models.
    """
    if created_models is None:
        created_models = {}

    lines = ["from pydantic import BaseModel", "from typing import List, Optional\n"]

    def write_model(model_name: str, fields: Dict[str, Any]):
        lines.append(f"class {model_name}(BaseModel):")
        if not fields:
            lines.append("    pass")
            return

        for fname, spec in fields.items():
            # Nested array of entity objects
            if spec.type == "array" and spec.items in ont.entities:
                sub_model_name = spec.items
                if sub_model_name not in created_models:
                    write_model(sub_model_name, ont.entities[sub_model_name].fields)
                    created_models[sub_model_name] = True
                type_str = f"List[{sub_model_name}]"
            elif spec.type == "array":
                item_type = TYPE_MAP.get(spec.items or "string", str)
                type_str = f"List[{item_type.__name__ if hasattr(item_type, '__name__') else item_type}]"
            else:
                type_str = TYPE_MAP[spec.type].__name__

            default = "..." if spec.required else "None"
            if spec.type == "array" and not spec.required:
                default = "[]"

            line = f"    {fname}: {type_str} = {default}" if spec.required else f"    {fname}: Optional[{type_str}] = {default}"
            lines.append(line)

    write_model(name, fields)
    return "\n".join(lines)

# -----------------------------
# Main routine
# -----------------------------
if __name__ == "__main__":
    ont = load_ontology()
    os.makedirs("models", exist_ok=True)
    os.makedirs("schemas", exist_ok=True)

    created_models = {}

    for entity_name, entity in ont.entities.items():
        # Build in-memory Pydantic model
        Model = make_pyd_model(entity_name, entity.fields, ont, created_models)

        # Write JSON Schema
        schema = Model.model_json_schema()
        with open(f"schemas/{entity_name}.schema.json", "w") as f:
            json.dump(schema, f, indent=2)

        # Write Python Pydantic model file
        code = make_pyd_model_code(entity_name, entity.fields, ont, {})
        with open(f"models/{entity_name}.py", "w") as f:
            f.write(code)

    print("✅ Generated Pydantic models in /models and JSON schemas in /schemas")
