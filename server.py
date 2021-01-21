import uvicorn
import json
from fastapi import FastAPI
from middleware.validators import ValidationMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes import taxii
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


app.include_router(taxii.router)
log_info('Galaxy server is running ..')

if __name__ == '__main__':
    uvicorn.run(app, port=4000, host='0.0.0.0')
