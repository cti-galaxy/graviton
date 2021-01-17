from fastapi import APIRouter
from fastapi.responses import JSONResponse

from controllers.taxii import TAXII

from config.schema.taxii import DiscoveryResponseModel


router = APIRouter()


@router.get("/taxii2",  response_model=DiscoveryResponseModel, tags=["exchange"])
async def roots_discovery():
    return TAXII.get_discovery()
