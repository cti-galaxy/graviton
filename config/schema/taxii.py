from pydantic import BaseModel
from typing import List, Optional

# /** Discovery Schema **\
# ####################### #

# / Base Models\


class DiscoveryFailed(BaseModel):
    message: str

# / Requests and Response Models\


class DiscoveryResponse(BaseModel):
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


class DiscoveryFailedResponse(BaseModel):
    status: str
    payload: DiscoveryFailed

    class Config:

        schema_extra = {
            "example": {
                "status": "fail",
                "payload": {
                    "message": "Error (D:1) Failed to Get Discovery Information .."
                }
            }
        }
