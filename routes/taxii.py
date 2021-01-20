from fastapi import APIRouter, Request
from typing import Optional
from fastapi.responses import JSONResponse

from controllers.taxii import TAXII

from config.schema.taxii import DiscoveryModel, APIRootModel, \
    StatusModel, GetCollectionsModel, ErrorMessageModel

MEDIA_TYPE = "application/taxii+json;version=2.1"

router = APIRouter()


@router.get("/taxii2",
            response_model=DiscoveryModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get information about the TAXII Server and any advertised API Roots",
            tags=["Discovery"])
async def roots_discovery(request: Request):
    """
    This Endpoint provides general information about a TAXII Server, including the advertised API Roots.
    """
    response = TAXII.get_discovery()
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)

