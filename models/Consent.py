from pydantic import BaseModel
from typing import List, Optional

class Consent(BaseModel):
    patient_signature: Optional[str] = None
    guardian_signature: Optional[str] = None
    date: str = ...
    consent_type: Optional[str] = None
    provider_signature: Optional[str] = None