from fastapi import APIRouter, Request
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
async def roots_discovery():
    """
    This Endpoint provides general information about a TAXII Server, including the advertised API Roots.
    """
    response = TAXII.roots_discovery()
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)


@router.get("/{api_root}/status/{status_id}",
            response_model=StatusModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get status information for a specific status ID",
            tags=["API Roots"])
async def get_status(api_root: str, status_id: str):
    """
    This Endpoint provides information about the status of a previous request
    """
    response = TAXII.get_status(api_root, status_id)
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)


@router.get("/{api_root}",
            response_model=APIRootModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get information about a specific API Root",
            tags=["API Roots"])
async def get_api_root_information(api_root: str):
    """
    This Endpoint can be used to help users and clients decide whether and how they want to interact with a specific API Root.
    Multiple API Roots MAY be hosted on a single TAXII Server. Often, an API Root represents a single trust group.
    """
    response = TAXII.get_api_root_information(api_root)
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)


@router.get("/",
            response_model=APIRootModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get information about the Default API Root",
            tags=["API Roots"])
async def get_default_root_information():
    """
    This Endpoint can be used to help users and clients decide whether and how they want to interact with the default API Root.
    """
    response = TAXII.get_default_root_information()
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)
