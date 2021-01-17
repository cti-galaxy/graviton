from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes import taxii
from middleware.logging import log_info


ORIGINS = ["http://localhost:3000"]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(taxii.router)

log_info('Galaxy server is running ..')

if __name__ == '__main__':
    uvicorn.run(app, port=4000, host='0.0.0.0')
