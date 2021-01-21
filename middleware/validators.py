import re
import json
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

CONSTANTS: dict = json.load(open('config/constants.json', encoding="utf8"))
EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class AcceptHeaderValidator(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        result = {}
        taxii_header_exists = False
        wrong_taxii_header = False
        response = await call_next(request)
        accept_header = request.headers.get("accept", "").replace(" ", "").split(",")
        for item in accept_header:
            item_header = re.match(r"^application/taxii\+json(;version=(\d\.\d))?$", item)
            if item_header:
                if len(item_header.groups()) >= 1:
                    version_str = item_header.group(2)
                    if version_str != "2.1":
                        wrong_taxii_header = True
                        break
                taxii_header_exists = True
                break
        if wrong_taxii_header:
            response = JSONResponse(status_code=int(EXCEPTIONS.get('UnsupportedAcceptHeader', {})['error_code']),
                                    content=EXCEPTIONS.get('UnsupportedAcceptHeader', {}))
        elif not taxii_header_exists:
            response = JSONResponse(status_code=int(EXCEPTIONS.get('AcceptHeaderInvalid', {})['error_code']),
                                    content=EXCEPTIONS.get('AcceptHeaderInvalid', {}))
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

