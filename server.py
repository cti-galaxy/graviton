import uvicorn
import json
from fastapi import FastAPI
from middleware.validators import ValidationMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.esdb import EsClient
from middleware.logging import log_info, log_error

from routes import discovery
from routes import collections
from routes import objects


EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json'))

es_client = EsClient()
es_up = es_client.is_alive()

log_info("Checking if ElasticSearch is Up!")

if es_up:
    es_client.es_prep()
    app = FastAPI(middleware=ValidationMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            content={
                "title": str(exc.detail),
                "error_code": str(exc.status_code)
            },
            status_code=exc.status_code
        )

    # TODO: Enforce Authorization
    # TODO: Enable Paging
    # TODO: Review Error Codes
    # TODO: Review The Custom Headers

    app.include_router(discovery.router)
    app.include_router(collections.router)
    app.include_router(objects.router)

    log_info('Galaxy is running ..')

else:
    log_error('Galaxy is not ready to start, having a problem connecting to ElasticSearch')

if __name__ == '__main__':

    uvicorn.run(app, port=4000, host='0.0.0.0')
