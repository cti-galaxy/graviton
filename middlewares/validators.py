import re
import json
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config.schema.exceptions import *

CONSTANTS: dict = json.load(open('config/constants.json'))


class AcceptHeaderValidator(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        header_found = False
        header_is_valid = False
        response = await call_next(request)
        accept_header = request.headers.get('accept', "").replace(" ", "").split(",")
        for item in accept_header:
            validation_result = re.match(r"^application/taxii\+json(;version=(\d\.\d))?$", item)
            if validation_result:
                if len(validation_result.groups()) >= 1:
                    version_str = validation_result.group(2)
                    if version_str != "2.1":
                        header_is_valid = False
                header_found = True
                break

        if header_found is False:
            print("Media type in the Accept header is invalid or not found", 406)
        elif header_is_valid is False:
            print ("Media type in the Accept header is invalid or not found", 406)

        return response



ValidationMiddleware = [
    Middleware(CORSMiddleware,
               allow_origins=CONSTANTS.get('origins'),
               allow_credentials=True,
               allow_methods=["*"],
               allow_headers=["*"]
               ),
    Middleware(AcceptHeaderValidator)
]

