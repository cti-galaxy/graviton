import json
from services.esdb import EsClient
from middleware.logging import log_info, log_error

SETTINGS = json.load(open('config/settings.json'))
TAXII_DEFAULT_DISCOVERY = json.load(open('config/defaults/data/discovery.json'))
TAXII_DEFAULT_ROOTS = [
    json.load(open('config/defaults/data/roots-feed1.json')),
    json.load(open('config/defaults/data/roots-feed2.json'))
]
TAXXI_DEFAULT_COLLECTIONS = [
    json.load(open('config/defaults/data/feeds-collection1.json')),
    json.load(open('config/defaults/data/feeds-collection2.json')),
    json.load(open('config/defaults/data/feeds-collection3.json')),
    json.load(open('config/defaults/data/feeds-collection4.json'))
]


class BackInit(object):

    es_client = EsClient()

    @classmethod
    def is_es_alive(cls):
        log_info("Checking if ElasticSearch is Up!")
        status = cls.es_client.is_alive()
        if status:
            log_info("ElasticSearch is Up!")
        else:
            log_error("ElasticSearch is Down!")
        return status

    @classmethod
    def es_prep(cls):
        log_info("Creating Galaxy Elasticsearch Indices")
        status = cls.es_client.es_load_defaults(
            discovery=TAXII_DEFAULT_DISCOVERY,
            roots=TAXII_DEFAULT_ROOTS,
            collections=TAXXI_DEFAULT_COLLECTIONS
        )
        if status:
            log_info("Default Data is Loaded")
        else:
            log_error("Failed to Load Default Data")
        return status

    @classmethod
    def ping_services(cls):
        es_pong = cls.is_es_alive()
        return es_pong

    @classmethod
    def services_prep(cls):
        cls.es_prep()
