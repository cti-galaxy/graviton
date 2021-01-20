import uvicorn
from fastapi import FastAPI
from middlewares.validators import ValidationMiddleware

from routes import taxii
from middlewares.logging import log_info


app = FastAPI(middleware=ValidationMiddleware)


app.include_router(taxii.router)
log_info('Galaxy server is running ..')

if __name__ == '__main__':
    uvicorn.run(app, port=4000, host='0.0.0.0')
