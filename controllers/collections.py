import json
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient
from elasticsearch.exceptions import NotFoundError

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class Collections(object):

    es_client = EsClient()

    @classmethod
    def get_collections(cls, api_root):
        log_debug(f'Request to Get all Collections under {api_root} Root')
        try:
            result = cls.es_client.get_docs(index=f'{api_root}-collections').get('data')
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
            return result
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionNotFoundException', {})

    @classmethod
    def get_collection_manifest(cls, api_root, **query_parameters):
        log_debug(f"Request to Get The objects Manifest of Collection: {query_parameters.get('collection_id')} "
                  f"in the Feed Root: {api_root}")
        try:
            results = cls.es_client.search_manifests(index=api_root,
                                                     query_parameters=query_parameters)
            return results
        except Exception as e:
            log_error(e)
            if query_parameters.get('next'):
                return EXCEPTIONS.get('NextNotFoundException', {})
            else:
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
