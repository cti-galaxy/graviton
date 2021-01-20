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
        validation_result = None
        request = await call_next(request)
        header_to_validate = request.headers.get('accept', "").replace(" ", "").split(",")
        if type(header_to_validate) == list:
            for item in header_to_validate:
                validation_result = re.match(self.header_value, item)
                print (validation_result)
        else:
            validation_result = re.match(self.header_value, header_to_validate)
            print(validation_result)

        return validation_result


ValidationMiddleware = [
    Middleware(CORSMiddleware,
               allow_origins=CONSTANTS.get('origins'),
               allow_credentials=True,
               allow_methods=["*"],
               allow_headers=["*"]
               ),
    Middleware(AcceptHeaderValidator)
]

