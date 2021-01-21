import json
from urllib.parse import urlparse
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class TAXII(object):

    es_client = EsClient()

    @classmethod
    def roots_discovery(cls):
        log_debug('Request to Get Discovery Info')

        try:
            result = cls.es_client.get_doc(index='galaxy-discovery', doc_id='discovery')
            return result['data']
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('DiscoveryException', {})

    @classmethod
    def get_api_root_information(cls, api_root):
        log_debug('Request to Get an API Root Information')
        api_root_list = cls.es_client.get_doc(index='galaxy-discovery', doc_id='discovery').get('data')['api_roots']
        if api_root in str(api_root_list):
            result = cls.es_client.get_doc(index=f'galaxy-{api_root}', doc_id=api_root)
            return result['data']['information']
        else:
            return EXCEPTIONS.get('APIRootNotFoundException')

    @classmethod
    def get_default_root_information(cls):
        log_debug('Request to Get Default API Root Information')
        try:
            default_api_root_url = cls.es_client.get_doc(index='galaxy-discovery', doc_id='discovery').get('data')['default']
            default_api_root = urlparse(default_api_root_url)[2].partition('/')[2].partition('/')[0]
            result = cls.es_client.get_doc(index=f'galaxy-{default_api_root}', doc_id=default_api_root)
            return result['data']['information']
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('DefaultAPIRootNotFoundException')

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
