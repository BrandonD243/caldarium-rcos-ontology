from fastapi import FastAPI, UploadFile, File
from ontology.loader import load_ontology
from ontology.generate_schemas import make_pyd_model
from pydantic import ValidationError
from ontology.utils import write_audit, sha256_bytes
import uvicorn, json

app = FastAPI(title="Caldarium Ontology Service")

@app.get("/v1/ontology/entities")
def list_entities():
    ont = load_ontology()
    return {"entities": list(ont.entities.keys())}

@app.post("/v1/validate/{entity_name}")
async def validate_entity(entity_name: str, file: UploadFile = File(...)):
    ont = load_ontology()

    # read uploaded bytes & hash for determinism
    raw_bytes = await file.read()
    file_hash = sha256_bytes(raw_bytes)

    if entity_name not in ont.entities:
        write_audit({
            "role": "validator", "actor": "brandon", "action": "validate_entity",
            "entity": entity_name, "status": "error", "reason": "unknown entity",
            "file_hash": file_hash
        })
        return {"ok": False, "error": "unknown entity"}

    try:
        Model = make_pyd_model(entity_name, ont.entities[entity_name].fields, ont)
        data = json.loads(raw_bytes.decode("utf-8"))
        Model(**data)


        # success
        write_audit({
            "role": "validator", "actor": "brandon", "action": "validate_entity",
            "entity": entity_name, "status": "success", "file_hash": file_hash,
            "schema_version": "registry_v1"
        })

        return {"ok": True}

    except ValidationError as e:
        write_audit({
            "role": "validator", "actor": "brandon", "action": "validate_entity",
            "entity": entity_name, "status": "failed_validation",
            "file_hash": file_hash, "errors": e.errors()
        })
        return {"ok": False, "errors": e.errors()}

    except Exception as e:
        write_audit({
            "role": "validator", "actor": "brandon", "action": "validate_entity",
            "entity": entity_name, "status": "exception",
            "file_hash": file_hash, "error": str(e)
        })
        return {"ok": False, "error": str(e)}
