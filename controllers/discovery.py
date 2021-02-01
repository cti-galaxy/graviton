import json
from urllib.parse import urlparse
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))


class Discovery(object):

    es_client = EsClient()

    @classmethod
    def roots_discovery(cls):
        log_debug('Request to Get Discovery Info')

        try:
            result = cls.es_client.get_doc(index='discovery', doc_id='discovery')
            return result['data']
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('DiscoveryException', {})

    @classmethod
    def get_api_root_information(cls, api_root):
        log_debug(f'Request to Get {api_root} Root Information')
        api_root_list = cls.es_client.get_doc(index='discovery', doc_id='discovery').get('data')['api_roots']
        if api_root in str(api_root_list):
            result = cls.es_client.get_doc(index='feeds', doc_id=api_root)
            return result['data']['information']
        else:
            return EXCEPTIONS.get('APIRootNotFoundException')

    @classmethod
    def get_default_root_information(cls):
        log_debug('Request to Get Default API Root Information')
        try:
            default_api_root_url = cls.es_client.get_doc(index='discovery', doc_id='discovery').get('data')['default']
            default_api_root = urlparse(default_api_root_url)[2].partition('/')[2].partition('/')[0]
            result = cls.es_client.get_doc(index='feeds', doc_id=default_api_root)
            return result['data']['information']
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('DefaultAPIRootNotFoundException')

    @classmethod
    def get_status(cls, api_root, status_id):
        log_debug(f'Request to Get the status of {status_id} from {api_root}')
        try:
            result = cls.es_client.get_doc(index=f'{api_root}-status', doc_id=status_id)
            return result['data']
        except Exception as e:
            log_error(e)
            return EXCEPTIONS.get('StatusNotFoundException')
