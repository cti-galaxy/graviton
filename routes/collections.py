from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.collections import Collections

from config.schema.taxii import Collection, CollectionsModel, \
    CollectionManifestModel, ErrorMessageModel

MEDIA_TYPE = "application/taxii+json;version=2.1"

router = APIRouter()


@router.get("/{api_root}/collections/{collection_id}/manifest",
            response_model=CollectionManifestModel,
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
    # TODO: Enforce Authorization
    # TODO: Enable Paging
    response = Collections.get_collection_manifest(api_root, collection_id)
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        if response.get('objects'):
            return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)
        elif response.get('error_code'):
            return JSONResponse(status_code=int(response.get('error_code')), content=response)
        else:
            return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=[])


@router.get("/{api_root}/collections/{collection_id}",
            response_model=Collection,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get information about a specific collection",
            tags=["Collections"])
async def get_collection(api_root: str, collection_id: str):
    """
    Defines TAXII API - Collections:
    Get Collection section (5.2) `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107535>`__

    Args:
        api_root (str): the base URL of the API Root
        collection_id (str): the `identifier` of the Collection being requested

    Returns:
        collection: A Collection Resource upon successful requests. Additional information
        `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107536>`__.

    """
    # TODO: Enforce Authorization
    response = Collections.get_collection(api_root, collection_id)
    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)


@router.get("/{api_root}/collections",
            response_model=CollectionsModel,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get information about all collections",
            tags=["Collections"])
async def get_collections(api_root: str):
    """
    Defines TAXII API - Collections:
    Get Collection section (5.1) `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107533>`__

    Args:
        api_root (str): the base URL of the API Root

    Returns:
        collections: A Collections Resource upon successful requests. Additional information
        `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107534>`__.

    """
    # TODO: Enforce Authorization
    # TODO: Enable Paging
    response = Collections.get_collections(api_root)
    if response.get('collections'):
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response)
    elif response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=[])

