from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.taxii import TAXII

from config.schema.taxii import DiscoveryModel, APIRootModel, StatusModel, GetCollectionsModel, ErrorMessageModel


router = APIRouter()


@router.get("/taxii2",  response_model=DiscoveryModel, responses={500: {"model": ErrorMessageModel}}, tags=["discovery"])
async def roots_discovery():
    response = TAXII.get_discovery()
    if response.get('status') == 'fail':
        return JSONResponse(status_code=500, content=response)
    else:
        return JSONResponse(status_code=200, content=response)
