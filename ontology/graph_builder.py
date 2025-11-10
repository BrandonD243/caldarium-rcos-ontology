# ontology/graph_builder.py

import json, glob, os
import networkx as nx
from loader import load_ontology

G = nx.DiGraph()

def add_node(node_id, ntype, **attrs):
    # Replace None values with safe defaults
    safe_attrs = {k: (v if v is not None else "") for k, v in attrs.items()}
    G.add_node(node_id, type=ntype, **safe_attrs)

def add_edge(src, dst, rel):
    G.add_edge(src, dst, relation=rel)

def idify(s: str) -> str:
    """Make a simple ID-friendly string from a name or value"""
    return s.lower().replace(" ", "_") if s else "unknown"

# -----------------------------
# Build graph from JSONs
# -----------------------------
# Invoices
for path in glob.glob("ground_truth/invoices/*.json"):
    d = json.load(open(path))
    pat_id = f"pat:{idify(d.get('patient_name'))}"
    enc_id = f"enc:{idify(d.get('patient_name'))}:{d.get('admission_date','')}"
    clm_id = f"clm:{os.path.basename(path).split('.')[0]}"

    add_node(pat_id, "Patient",
             name=d.get("patient_name"),
             dob=d.get("patient_dob"),
             patient_id=d.get("patient_id"))

    add_node(enc_id, "Encounter",
             admission_date=d.get("admission_date"),
             discharge_date=d.get("discharge_date"),
             provider_name=d.get("provider_name"),
             provider_address_name=d.get("provider_address_name"))

    add_node(clm_id, "Claim",
             total_amount=d.get("total_amount"),
             invoice_number=d.get("invoice_number"),
             line_items=d.get("line_items"))

    add_edge(pat_id, enc_id, "has_encounter")
    add_edge(enc_id, clm_id, "generates_claim")

# Consents
for path in glob.glob("ground_truth/consents/*.json"):
    d = json.load(open(path))
    pat_id = f"pat:{idify(d.get('patient_name'))}"
    enc_id = f"enc:{idify(d.get('patient_name'))}:{d.get('admission_date','')}"
    consent_id = f"cons:{os.path.basename(path).split('.')[0]}"

    add_node(consent_id, "Consent",
             consent_type=d.get("consent_type"),
             date=d.get("date"),
             patient_signature=d.get("patient_signature"),
             guardian_signature=d.get("guardian_signature"),
             provider_signature=d.get("provider_signature"))

    add_edge(pat_id, consent_id, "has_consent")
    if d.get("admission_date") or enc_id in G.nodes:
        add_edge(enc_id, consent_id, "related_to_encounter")

# -----------------------------
# Write GEXF
# -----------------------------
os.makedirs("output/reports", exist_ok=True)
nx.write_gexf(G, "output/reports/ontology_graph.gexf")
print("✅ Graph nodes:", G.number_of_nodes(), "edges:", G.number_of_edges())
