from pydantic import BaseModel
from typing import List, Optional

# /** Discovery Schema **\
# ####################### #

# / Requests and Response Models\


class DiscoveryResponseModel(BaseModel):
    api_roots: list
    contact: str
    default: str
    description: str
    title: str

    class Config:
        schema_extra = {
            "example": {
                "title": "Galaxy TAXII Server",
                "description": "This TAXII Server contains a listing of Stix2 Collections",
                "contact": "ayman@lab.local",
                "default": "http://localhost:6000/feed1/",
                "api_roots": [
                    "http://localhost:6000/feed1/",
                    "http://localhost:6000/feed2/"
                ]
            }
        }