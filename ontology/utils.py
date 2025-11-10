import json, os, time, hashlib

def write_audit(event: dict, path="output/logs/ontology_audit.jsonl"):
    """Append an audit event to a JSONL log file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    event = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **event}
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")

def sha256_bytes(b: bytes) -> str:
    """Return the SHA-256 hash (hex digest) of given bytes."""
    return hashlib.sha256(b).hexdigest()
