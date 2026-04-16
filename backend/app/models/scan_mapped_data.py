from pydantic import BaseModel
from typing import List
from .web_input import WebInput

class ScanMappedData(BaseModel):
    url: str
    inputs: List[WebInput]
