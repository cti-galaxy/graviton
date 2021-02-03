from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, TypeVar


# /** TAXII 2.1 Pydantic Schema **\
# ####################### #

# / Base Models\

identifier = TypeVar('identifier', bound=UUID4)


class StatusDetails(BaseModel):
    id: str = Field(description='The identifier of the object that succeed, is pending, or failed to be created.')
    version: str = Field(description='The version of the object that succeeded, is pending, or failed to be created.')
    message: Optional[str] = Field(description='A message indicating more information about the object being created, '
                                               'its pending state, or why the object failed to be created.')


class Collection(BaseModel):
    id: identifier = Field(description='The id property universally and uniquely identifies this Collection.')
    title: str = Field(description='A human readable plain text title used to identify this Collection.')
    description: Optional[str] = Field(description='A human readable plain text description for this Collection.')
    alias: Optional[str] = Field(description='A human readable collection name '
                                             'that can be used on systems to alias a collection ID. ')
    can_read: bool = Field(description='Indicates if the requester can read (i.e., GET) objects from this Collection. '
                                       'If true, users are allowed to access the Get Objects, Get an Object, '
                                       'or Get Object Manifests endpoints for this Collection. '
                                       'If false, users are not allowed to access these endpoints.')
    can_write: bool = Field(description='Indicates if the the requester can write (i.e., POST) objects to '
                                        'this Collection. If true, users are allowed to access the Add Objects '
                                        'endpoint for this Collection. If false, users are not allowed to access '
                                        'this endpoint.')
    media_types: Optional[List[str]] = Field(description='A list of supported media types for Objects '
                                                         'in this Collection.')

    class Config:
        schema_extra = {
            "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
            "title": "High Value Indicator Collection",
            "description": "This data collection contains high value IOCs",
            "can_read": True,
            "can_write": False,
            "media_types": [
                "application/stix+json;version=2.1"
            ]
        }


class ManifestRecord(BaseModel):
    id: str = Field(description='The identifier of the object that this manifest entry describes.')
    date_added: datetime = Field(description='The date and time this object was added.')
    version: str = Field(description='The version of this object.')
    media_type: Optional[str] = Field(description='The media type that this specific version of '
                                                  'the object can be requested in.')


class Envelope(BaseModel):
    more: Optional[bool] = Field(description='This property identifies if there is more content available based on '
                                             'the search criteria. The absence of this property means the value '
                                             'is false.')
    objects: Optional[List[dict]] = Field(description='This property contains one or more STIX Objects. '
                                                      'Objects in this list MUST be a STIX Object (SDO or SRO),'
                                                      ' a Language Content object, or a Marking Definition object.')


# / Response Models\

class DiscoveryModel(BaseModel):
    title: str = Field(description='A human readable plain text name used to identify this server.')
    description: Optional[str] = Field(description='A human readable plain text description for this server.')
    contact: Optional[str] = Field(description='The human readable plain text contact information for this server'
                                               ' and/or the administrator of this server. ')
    default: Optional[str] = Field(description='The default API Root that a TAXII Client MAY use. '
                                               'Absence of this property indicates that there is no default API Root.')
    api_roots: Optional[List[str]] = Field(description='A list of URLs that identify known API Roots. This list MAY be '
                                                       'filtered on a per-client basis. ')

    class Config:
        schema_extra = {
            "example": {
                "title": "Galaxy TAXII Server",
                "description": "This TAXII Server contains a listing of Stix2 Collections",
                "contact": "ayman@lab.local",
                "default": "http://localhost:6000/feed1/",
                "api_roots": [
                    "http://localhost:6000/feed1/",
                    "http://localhost:6000/feed2/"
                ]
            }
        }


class APIRootModel(BaseModel):
    title: str = Field(description='A human readable plain text name used to identify this API instance.')
    description: Optional[str] = Field(description='A human readable plain text description for this API Root.')
    versions: List[str] = Field(description='The list of TAXII versions that this API Root is compatible with.')
    max_content_length: int = Field(description='The maximum size of the request body in octets (8-bit bytes) '
                                                'that the server can support.')

    class Config:
        schema_extra = {
            "example": {
                "title": "External Feeds",
                "description": "A Test External Feeds .",
                "versions": [
                    "application/taxii+json;version=2.1"
                ],
                "max_content_length": 9765625
            }
        }


class StatusModel(BaseModel):
    id: identifier = Field(description='The identifier of this Status resource.')
    status: str = Field(description='The overall status of a previous POST request where an HTTP 202 (Accept) '
                                    'was returned. The value of this property MUST be one of complete or pending.')
    request_timestamp: Optional[datetime] = Field(description='The datetime of the request that this status '
                                                              'resource is monitoring.')
    total_count: int = Field(description='The total number of objects that were in the request,'
                                         ' which would be the number of objects in the envelope.')
    success_count: int = Field(description='The number of objects that were successfully created.')
    successes: Optional[List[StatusDetails]] = Field(description='A list of objects that was successfully processed.')
    failure_count: int = Field(description='The number of objects that failed to be created.')
    failures: Optional[List[StatusDetails]] = Field(description='A list of objects that was not '
                                                                'successfully processed.')
    pending_count: int = Field(description='The number of objects that have yet to be processed.')
    pendings: Optional[List[StatusDetails]] = Field(description='A list of objects that have yet to be processed.')

    class Config:
        schema_extra = {
            "id": "2d086da7-4bdc-4f91-900e-d77486753710",
            "status": "pending",
            "request_timestamp": "2016-11-02T12:34:34.12345Z",
            "total_count": 4,
            "success_count": 1,
            "successes": [
                {
                    "id": "indicator--c410e480-e42b-47d1-9476-85307c12bcbf",
                    "version": "2018-05-27T12:02:41.312Z"
                }
            ],
            "failure_count": 1,
            "failures": [
                {
                    "id": "malware--664fa29d-bf65-4f28-a667-bdb76f29ec98",
                    "version": "2018-05-28T14:03:42.543Z",
                    "message": "Unable to process object"
                }
            ],
            "pending_count": 2,
            "pendings": [
                {
                    "id": "indicator--252c7c11-daf2-42bd-843b-be65edca9f61",
                    "version": "2018-05-18T20:16:21.148Z"
                },
                {
                    "id": "relationship--045585ad-a22f-4333-af33-bfd503a683b5",
                    "version": "2018-05-15T10:13:32.579Z"
                }
            ]
        }


class CollectionsModel(BaseModel):
    collections: Optional[Collection] = Field(description='A list of Collections. If there are no Collections, '
                                                          ' this key is omitted.')

    class Config:
        schema_extra = {
            "collections": [
                {
                    "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
                    "title": "High Value Indicator Collection",
                    "description": "This data collection is for collecting high value IOCs",
                    "can_read": True,
                    "can_write": True,
                    "media_types": [
                        "application/stix+json;version=2.0",
                        "application/stix+json;version=2.1"
                    ]
                },
                {
                    "id": "9f0725cb-4bc3-47c3-aba6-99cb97ba4f52",
                    "title": "IMDDOS Botnet Report",
                    "description": "IMDDOS Botnet Report",
                    "can_read": True,
                    "can_write": True,
                    "media_types": [
                        "application/stix+json;version=2.1"
                    ]
                },
                {
                    "id": "ac946f1d-6a0e-4a9d-bc83-3f1f3bfda6ba",
                    "title": "Fireeye's Poison Ivy Report",
                    "description": "Fireeye's Poison Ivy Report",
                    "can_read": True,
                    "can_write": True,
                    "media_types": [
                        "application/stix+json;version=2.1"
                    ]
                },
                {
                    "id": "cf20f99b-3ed2-4a9f-b4f1-d660a7fc8241",
                    "title": "Mandiant's APT1 Report",
                    "description": "Mandiant's APT1 Report",
                    "can_read": True,
                    "can_write": True,
                    "media_types": [
                        "application/stix+json;version=2.1"
                    ]
                }
            ]
        }


class CollectionManifestModel(BaseModel):
    objects: Optional[ManifestRecord] = Field(description='The list of manifest entries for objects returned by the '
                                                          'request. If there are no manifest-record items in the list, '
                                                          'this key is omitted, and the response is an empty '
                                                          'object.')

    class Config:
        schema_extra = {
            "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
            "title": "High Value Indicator Collection",
            "description": "This data collection contains high value IOCs",
            "can_read": True,
            "can_write": False,
            "media_types": [
                "application/stix+json;version=2.1"
            ]
        }


# / Response Models\


class ErrorMessageModel(BaseModel):
    title: str = Field(description='A human readable plain text title for this error.')
    description: Optional[str] = Field(description='A human readable plain text description that gives details about '
                                                   'the error or problem that was encountered by the application.')
    error_id: Optional[str] = Field(description='The error id for this error type.')
    error_code: Optional[str] = Field(description='The HTTP error code applicable to this error.')
    http_status: Optional[str] = Field(description='The HTTP status code applicable to this error.')
    external_details: Optional[str] = Field(description='A URL that points to additional details. For example, '
                                                        'this could be a URL pointing to a knowledge base article '
                                                        'describing the error code.')
    details: Optional[str] = Field(description='The details property captures additional server-specific '
                                               'details about the error.')

    class Config:

        schema_extra = {
            "example": {
                "title": "Error condition XYZ",
                "description": "This error is caused when the application tries to access data...",
                "error_id": "1234",
                "error_code": "581234",
                "http_status": "409",
                "external_details": "http://example.com/ticketnumber1/errorid-1234",
                "details": {
                    "somekey1": "somevalue",
                    "somekey2": "some other value"
                }
            }
        }
