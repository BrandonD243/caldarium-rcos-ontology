from pydantic import BaseModel
from typing import List, Optional

class Encounter(BaseModel):
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    provider_name: Optional[str] = None
    provider_address_name: Optional[str] = None