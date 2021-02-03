from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional

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
async def get_collection_manifest(
        api_root: str = Path(..., description='the base URL of the API Root'),
        collection_id: str = Path(..., description='the identifier of the Collection being requested'),
        added_after: Optional[str] = Query(None, description="a single timestamp (e.g., ?added_after=...)"),
        limit: Optional[str] = Query(None, description='a single timestamp  (e.g., ?limit=...)'),
        next: Optional[str] = Query(None, description='a single string (e.g., ?next=...)'),
        id: Optional[str] = Query(None, description='an id(s) of an object  (e.g., ?match[id]=...)'),
        type: Optional[str] = Query(None, description='the type(s) of an object (e.g., ?match[type]=...)'),
        version: Optional[str] = Query(None, description='the version(s) of an object (e.g., ?match[version]=...)'),
        spec_version: Optional[str] = Query(None, description='the specification version(s) (e.g., ?match[version]=...)')
):
    """
    Defines TAXII API - Collections:
    Get Object Manifests section (5.3) `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107537>`__

    Returns:
        manifest: A Manifest Resource upon successful requests. Additional information
        `here <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107538>`__.

    """
    # TODO: Enforce Authorization
    # TODO: Enable Paging
    response = Collections.get_collection_manifest(
        api_root=api_root,
        collection_id=collection_id,
        added_after=added_after,
        limit=limit,
        next=next,
        id=id,
        type=type,
        version=version,
        spec_version=spec_version
    )
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

