import json
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class Objects(object):

    es_client = EsClient()

    @classmethod
    def get_collection_objects(cls, api_root, collection_id):
        log_debug(f'Request to Get The objects of Collection: {collection_id} in the Feed Root: {api_root}')

        try:
            result = cls.es_client.get_doc(index=f'{api_root}-collections', doc_id=collection_id)['data']['objects']
            return {
                'objects': result
            }
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('CollectionNotFoundException', {})
