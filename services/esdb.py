import time
import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import QueryString

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

        collections = []
        manifests_data = []
        objects_data = []

        self.client = Elasticsearch(hosts=host)

        if discovery_data is None:
            discovery_data = self.TAXII_DEFAULT_DISCOVERY
        if roots_data is None:
            roots_data = self.TAXII_DEFAULT_ROOTS
        if status_data is None:
            status_data = self.TAXXI_DEFAULT_STATUS
        if collections_data is None:
            collections_data = self.TAXXI_DEFAULT_COLLECTIONS
            for collection in collections_data:
                manifests = collection['_source'].get('manifest')
                if manifests:
                    for manifest in manifests:
                        manifest['_collection'] = collection.get('_id')
                        manifests_data.append(manifest)
            for collection in collections_data:
                objects = collection['_source'].get('objects')
                if objects:
                    for object in objects:
                        object['_collection'] = collection.get('_id')
                        objects_data.append(object)
            for collection in collections_data:
                collection['_source'].pop("manifest", None)
                collection['_source'].pop("responses", None)
                collection['_source'].pop("objects", None)
                collections.append(collection)

        log_info("Checking if ElasticSearch is Up!")
        if self.client.ping():
            log_info("ElasticSearch is Up!")
            log_debug("Loading Data ..")
            try:
                # Create Discovery Index and Load Discovery Data
                if not self.client.indices.exists(discovery_data.get('_index')):
                    log_info(f"Loading default data in {discovery_data.get('_index')} index...")
                    self.client.indices.create(index=discovery_data.get('_index'))
                    helpers.bulk(self.client, [discovery_data])
                for root in roots_data:
                    # Create API Roots Index and Load API Roots Data
                    if not self.client.indices.exists(root.get('_index')):
                        log_info(f"Loading default data in {root.get('_index')} index...")
                        self.client.indices.create(index=root.get('_index'))
                        helpers.bulk(self.client, roots_data)
                    # Create Status Index and Load Status Data
                    if not self.client.indices.exists(f"{root.get('_id')}-status"):
                        log_info(f"Loading default data in status index...")
                        self.client.indices.create(index=f"{root.get('_id')}-status")
                        helpers.bulk(self.client, status_data)
                    # Create Collections Index and Load Collections Data
                    if not self.client.indices.exists(f"{root.get('_id')}-collections"):
                        log_info(f"Loading default data in collections index...")
                        self.client.indices.create(index=f"{root.get('_id')}-collections")
                        helpers.bulk(self.client, collections)
                    # Create Manifest Index and Load Manifest Data
                    if not self.client.indices.exists(f"{root.get('_id')}-manifests"):
                        log_info(f"Loading manifests data in manifests index...")
                        self.client.indices.create(index=f"{root.get('_id')}-manifests")
                        helpers.bulk(self.client, manifests_data)
                    # Create Objects Index and Load Objects Data
                    if not self.client.indices.exists(f"{root.get('_id')}-objects"):
                        log_info(f"Loading objects data in object index...")
                        self.client.indices.create(index=f"{root.get('_id')}-objects")
                        helpers.bulk(self.client, objects_data)

            except Exception as e:
                log_error(e)
        else:
            log_error("ElasticSearch is Down!")

    # Object Methods

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
        except es_exceptions.NotFoundError as e:
            raise e

    def search(self, index: str, query: str = None, fields: str = None,
               base_page: int = 0, size: int = 100, sort_field: str = None, sort_order: str = None):
        try:
            query_string = QueryString(query=query)
            search = Search(using=self.client, index=index).query(query_string)[base_page:base_page + size]

            if fields is not None:
                fields = fields.split(',')
                search = search.source(fields)

            if sort_field is not None:
                search = search.sort({sort_field: {'order': sort_order}})

            search_results = search.execute().to_dict()
            results = []
            for result in search_results['hits']['hits']:
                response = {}
                response.update(result['_source'])
                response.update({
                    'id': result['_id']
                })
                results.append(response)
            return {
                "data": results,
                "total": search_results['hits']['total']['value'],
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
