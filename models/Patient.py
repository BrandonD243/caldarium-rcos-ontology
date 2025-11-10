from pydantic import BaseModel
from typing import List, Optional

class Patient(BaseModel):
    patient_name: str = ...
    patient_dob: Optional[str] = None
    patient_id: Optional[str] = None