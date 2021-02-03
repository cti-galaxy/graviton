import json
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient
from elasticsearch.exceptions import NotFoundError

from .common import Helper

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class Collections(object):

    es_client = EsClient()

    @classmethod
    def get_collections(cls, api_root):
        log_debug(f'Request to Get all Collections under {api_root} Root')
        try:
            result = cls.es_client.get_docs(index=f'{api_root}-collections').get('data')
            for collection in result:
                collection.pop("manifest", None)
                collection.pop("responses", None)
                collection.pop("objects", None)

            return {
                'collections': result
            }
        except NotFoundError as e:
            log_error(e)
            return EXCEPTIONS.get('APIRootNotFoundException', {})
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionsNotFoundException', {})

    @classmethod
    def get_collection(cls, api_root, collection_id):
        log_debug(f'Request to Get Collection {collection_id} from Feed: {api_root}')
        try:
            result = cls.es_client.get_doc(index=f'{api_root}-collections', doc_id=collection_id).get('data')
            result.pop("manifest", None)
            result.pop("responses", None)
            result.pop("objects", None)
            return result
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionNotFoundException', {})
    """
    @classmethod
    def get_collection_manifest(cls, api_root, collection_id, **query_parameters):
        if query_parameters.get('added_after'):
            print ('test')
        log_debug(f'Request to Get The objects Manifest of Collection: {collection_id} in the Feed Root: {api_root}')
        try:
            result = cls.es_client.get_doc(index=f'{api_root}-collections', doc_id=collection_id)['data']['manifest']
            return {
                'objects': result
            }
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionNotFoundException', {})
    """

    @classmethod
    def get_collection_manifest(cls, api_root, **query_parameters):
        log_debug(f"Request to Get The objects Manifest of Collection: {query_parameters.get('collection_id')} "
                  f"in the Feed Root: {api_root}")
        try:
            query = f"_id = {query_parameters.get('collection_id')}"
            #result = cls.es_client.search(index=f'{api_root}-collections', query=query)['data']['manifest']
            result = {}
            return {
                'objects': result
            }
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionNotFoundException', {})

    @classmethod
    def post_objects(cls, cti_objects):
        log_info(f'Request to Post {len(cti_objects)} Objects')

        result = {}
        try:
            entry = cls.es_client.store_docs(index="stix21", data=cti_objects.dict().get('objects'))
            result["status"] = 'success'
            result["payload"] = entry
            return result
        except Exception as e:
            log_error(e)
            result["status"] = 'fail'
            result["payload"] = {
                "message": "Error (E:4) while posting the object .."
            }
            return result

    @classmethod
    def delete_object(cls, object_id):
        log_info(f'Request to Delete Object: {object_id}')
        result = {}
        res = cls.es_client.delete_doc(index="stix21", doc_id=object_id)
        if res:
            result["status"] = 'success'
            result["payload"] = res
            return result
        else:
            result["status"] = 'fail'
            result["payload"] = {
                "message": "Error (E:5) Object not found .."
            }
            return result
