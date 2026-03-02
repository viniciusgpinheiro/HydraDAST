from pydantic import BaseModel
from typing import List
from WebInput import WebInput

class ScanMappedData(BaseModel):
    url: str
    inputs: List[WebInput]
