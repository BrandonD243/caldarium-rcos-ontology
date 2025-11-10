from pydantic import BaseModel
from typing import List, Optional

class Claim(BaseModel):
    total_amount: float = ...
    invoice_number: Optional[str] = None
    line_items: List[str] = ...