import uvicorn
import json
from fastapi import FastAPI
from middleware.validators import ValidationMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes import discovery
from routes import collections
from routes import objects

from middleware.logging import log_info

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json'))


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

log_info('Galaxy server is running ..')

if __name__ == '__main__':
    uvicorn.run(app, port=4000, host='0.0.0.0')
