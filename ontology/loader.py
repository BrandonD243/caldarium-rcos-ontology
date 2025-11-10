from pydantic import BaseModel, ValidationError, model_validator
from typing import Dict, Optional, Literal
import yaml, pathlib

ScalarType = Literal["string","date","decimal","integer","boolean","array"]

class FieldSpec(BaseModel):
    type: ScalarType
    required: bool = False
    sensitive: bool = False
    items: Optional[ScalarType] = None  # only for arrays

    @model_validator(mode="before")
    def check_array_items(cls, values):
        t = values.get("type")
        items = values.get("items")
        if t != "array" and items is not None:
            raise ValueError("Only fields of type 'array' can have 'items'")
        if t == "array" and items is None:
            raise ValueError("Array fields must define 'items'")
        return values

class RelationSpec(BaseModel):
    target: str
    cardinality: Literal["one","many"]

class EntitySpec(BaseModel):
    fields: Dict[str, FieldSpec]
    relations: Dict[str, RelationSpec] = {}

class Ontology(BaseModel):
    entities: Dict[str, EntitySpec]

def load_ontology(path="ontology/registry_v1.yaml") -> Ontology:
    data = yaml.safe_load(pathlib.Path(path).read_text())
    return Ontology(**data)

if __name__ == "__main__":
    try:
        ont = load_ontology()
        print("Ontology loaded. Entities:", ", ".join(ont.entities.keys()))
    except ValidationError as e:
        print("Ontology YAML is invalid:\n", e)
        raise
