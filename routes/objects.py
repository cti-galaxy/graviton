from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.objects import Objects

from config.schema.taxii import Envelope, ErrorMessageModel

MEDIA_TYPE = "application/taxii+json;version=2.1"

router = APIRouter()


@router.get("/{api_root}/collections/{collection_id}/objects",
            response_model=Envelope,
            responses={500: {"model": ErrorMessageModel}},
            summary="Get all objects from a collection.",
            tags=["Objects"])
async def get_objects(api_root: str, collection_id: str):
    """
    Defines TAXII API - Collections:
        Get Objects section (`5.4 <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107539>`__)
        and Add Objects section (`5.5 <https://docs.oasis-open.org/cti/taxii/v2.1/cs01/taxii-v2.1-cs01.html#_Toc31107540>`__)

    Args:
        api_root (str): the base URL of the API Root
        collection_id (str): the `identifier` of the Collection being requested

    Returns:
        resource:
            GET -> An Envelope Resource upon successful requests.
            POST -> An Status Resource upon successful requests.

    """
    # TODO: Enforce Authorization
    # TODO: Enable Paging
    response = Objects.get_collection_objects(api_root, collection_id)

    if response.get('error_code'):
        return JSONResponse(status_code=int(response.get('error_code')), content=response)
    else:
        added_first = 'test' #response.get('objects')[0:]
        added_last = 'test1' #response.get('objects')[-1:]
        headers = {
            'X-TAXII-Date-Added-First': added_first,
            'X-TAXII-Date-Added-Last': added_last
        }
        return JSONResponse(status_code=200, media_type=MEDIA_TYPE, content=response, headers=headers)
