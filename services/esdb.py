import time
import json
from elasticsearch import Elasticsearch, helpers
from middleware.logging import log_debug, log_info, log_error


class EsClient:

    # Class Attributes
    default_settings = json.load(open('config/settings.json', encoding="utf8"))
    SETTINGS = json.load(open('config/settings.json', encoding="utf8"))
    TAXII_DEFAULT_DISCOVERY = json.load(open('config/defaults/data/discovery.json', encoding="utf8"))
    TAXII_DEFAULT_ROOTS = [
        json.load(open('config/defaults/data/roots-feed1.json', encoding="utf8")),
        json.load(open('config/defaults/data/roots-feed2.json', encoding="utf8"))
    ]
    TAXXI_DEFAULT_COLLECTIONS = [
        json.load(open('config/defaults/data/feeds-collection1.json', encoding="utf8")),
        json.load(open('config/defaults/data/feeds-collection2.json', encoding="utf8")),
        json.load(open('config/defaults/data/feeds-collection3.json', encoding="utf8")),
        json.load(open('config/defaults/data/feeds-collection4.json', encoding="utf8"))
    ]
    TAXXI_DEFAULT_STATUS = [
        json.load(open('config/defaults/data/feeds-status1.json', encoding="utf8")),
        json.load(open('config/defaults/data/feeds-status2.json', encoding="utf8"))
    ]

    # Constructor
    def __init__(self,
                 host=SETTINGS.get('services')['elasticsearch']['host'],
                 discovery_data=None,
                 roots_data=None,
                 collections_data=None,
                 status_data=None
                 ):
        if discovery_data is None:
            discovery_data = self.TAXII_DEFAULT_DISCOVERY
        if collections_data is None:
            collections_data = self.TAXXI_DEFAULT_COLLECTIONS
        if roots_data is None:
            roots_data = self.TAXII_DEFAULT_ROOTS
        if status_data is None:
            status_data = self.TAXXI_DEFAULT_STATUS

        self.client = Elasticsearch(hosts=host)

        log_info("Checking if ElasticSearch is Up!")
        if self.client.ping():
            log_info("ElasticSearch is Up!")
            log_debug("Loading Data ..")
            try:
                if not self.client.indices.exists(discovery_data.get('_index')):
                    log_info(f"Loading default data in {discovery_data.get('_index')} index...")
                    self.client.indices.create(index=discovery_data.get('_index'))
                    helpers.bulk(self.client, [discovery_data])
                for root in roots_data:
                    if not self.client.indices.exists(root.get('_index')):
                        log_info(f"Loading default data in {root.get('_index')} index...")
                        self.client.indices.create(index=root.get('_index'))
                        helpers.bulk(self.client, [roots_data])

                for status in status_data:
                    if not self.client.indices.exists(status.get('_index')):
                        log_info(f"Loading default data in {status.get('_index')} index...")
                        self.client.indices.create(index=status.get('_index'))
                        helpers.bulk(self.client, [status_data])

                for collection in collections_data:
                    if not self.client.indices.exists(collection.get('_index')):
                        log_info(f"Loading default data in {collection.get('_index')} index...")
                        self.client.indices.create(index=collection.get('_index'))
                        helpers.bulk(self.client, [collections_data])

            except Exception as e:
                log_error(e)
        else:
            log_error("ElasticSearch is Down!")

    # Methods

    def get_docs(self, index: str):
        try:
            res = self.client.search(index=index, size=10, sort='_id')
            results = []
            for result in res['hits']['hits']:
                response = {}
                response.update(result['_source'])
                response.update({
                    'id': result['_id']
                })
                results.append(response)
            return {
                "data": results,
                "total": res['hits']['total']['value'],
            }
        except Exception as e:
            log_error(e)
            raise

    def get_doc(self, index: str, doc_id: str):
        try:
            res = self.client.get(index=index, id=doc_id)
            return {
                "data": res.get('_source'),
            }
        except Exception as e:
            log_error(e)
            raise

    def store_doc(self, index: str, data: object,  doc_id=int(round(time.time() * 1000))):
        try:
            res = self.client.index(
                index=index,
                id=doc_id,
                body=data,
                refresh='wait_for'
            )
            return {
                "index": res['_index'],
                "id": res['_id'],
                "result": res['result']
            }
        except Exception as e:
            log_error(e)
            raise

    def store_docs(self, index: str, data: list):
        try:
            def yield_bulk_data(bulk_data):
                for doc in bulk_data:
                    yield {
                        "_index": index,
                        "_id": doc['id'],
                        "_source": doc
                    }
            res = helpers.bulk(
                self.client,
                yield_bulk_data(data)
            )
            return {
                "result": res
            }
        except Exception as e:
            log_error(e)
            raise

    def delete_doc(self, index: str, doc_id: str):
        try:
            res = self.client.delete(index=index, id=doc_id)
            return {
                "index": res['_index'],
                "id": res['_id'],
                "result": res['result']
            }
        except Exception as e:
            log_error(e)
            raise

    def delete_doc_by_query(self, index: str, query: dict):
        try:
            res = self.client.delete_by_query(index=index, body=query)
            return {
                "index": index,
                "result": res
            }
        except Exception as e:
            log_error(e)
            raise

    def update_doc(self, index: str, data: object,  doc_id: str):
        try:
            res = self.client.update(
                index=index,
                id=doc_id,
                body={
                    "doc": data
                },
                refresh='wait_for'
            )
            return {
                "index": res['_index'],
                "id": res['_id'],
                "result": res
            }
        except Exception as e:
            log_error(e)
            raise
