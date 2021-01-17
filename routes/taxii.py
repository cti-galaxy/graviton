from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.taxii import TAXII

from config.schema.taxii import DiscoveryResponse, DiscoveryFailedResponse


router = APIRouter()


@router.get("/taxii2",  response_model=DiscoveryResponse, responses={500: {"model": DiscoveryFailedResponse}}, tags=["discovery"])
async def roots_discovery():
    response = TAXII.get_discovery()
    if response.get('status') == 'fail':
        return JSONResponse(status_code=500, content=response)
    else:
        return response
