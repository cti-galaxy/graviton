from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.collections import Collections

from config.schema.taxii import APIRootModel, \
    GetCollectionManifestModel, ErrorMessageModel

MEDIA_TYPE = "application/taxii+json;version=2.1"

router = APIRouter()


@router.get("/{api_root}/collections/{collection_id}/manifest",
            response_model=GetCollectionManifestModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get manifest information about the contents of a specific collection.",
            tags=["Collections"])
async def get_collection_manifest(api_root: str, collection_id: str):
    """
    Defines TAXII API - Collections:
    Get Object Manifests section (5.3) `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107537>`__

    Args:
        api_root (str): the base URL of the API Root
        collection_id (str): the `identifier` of the Collection being requested

    Returns:
        manifest: A Manifest Resource upon successful requests. Additional information
        `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107538>`__.

    """
    response = Collections.get_collection_manifest(api_root, collection_id)
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        if response.get('objects'):
            return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)
        else:
            return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=[])


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
    response = Discovery.get_api_root_information(api_root)
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
    response = Discovery.get_default_root_information()
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)
