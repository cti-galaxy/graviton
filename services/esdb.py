import time
import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import QueryString, Range
from middleware.logging import log_debug, log_info, log_error
from os import environ, path
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class EsClient:

    # Class Attributes
    SETTINGS = json.load(open('config/settings.json', encoding="utf8"))
    USERNAME = 'elastic'
    PASSWORD = environ.get('ELASTIC_PASSWORD')


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
                 host: str = SETTINGS.get('services')['elasticsearch']['host'],
                 port: str = SETTINGS.get('services')['elasticsearch']['port'],
                 scheme: str = SETTINGS.get('services')['elasticsearch']['scheme'],
                 username: str = USERNAME,
                 password: str = PASSWORD,
                 discovery_data: dict = None,
                 roots_data: dict = None,
                 collections_data: dict = None,
                 status_data: dict = None,
                 verify_certs: bool = bool(SETTINGS.get('services')['elasticsearch']['verify_certs']) or False
                 ):
        self.client = Elasticsearch([host], http_auth=(username, password), scheme=scheme, port=port,
                                    verify_certs=verify_certs)
        self.discovery_data = discovery_data
        self.roots_data = roots_data
        self.collections_data = collections_data
        self.status_data = status_data

    # Object Methods
    def is_alive(self):
        return self.client.ping()

    def es_prep(self):
        try:
            collections = []
            manifests_data = []
            objects_data = []

            # Prepare Discovery Data
            if not self.discovery_data:
                self.discovery_data = self.TAXII_DEFAULT_DISCOVERY
            if not self.client.indices.exists(self.discovery_data.get('_index')):
                log_info(f"Loading default data in {self.discovery_data.get('_index')} index...")
                # Create The Discovery Index
                self.client.indices.create(index=self.discovery_data.get('_index'))
                # Load The Discovery Data
                helpers.bulk(self.client, [self.discovery_data])

            # Prepare API Roots Data
            if not self.roots_data:
                self.roots_data = self.TAXII_DEFAULT_ROOTS
            for root in self.roots_data:
                if not self.client.indices.exists(root.get('_index')):
                    log_info(f"Loading default data in {root.get('_index')} index...")
                    # Create The API Roots Index
                    self.client.indices.create(index=root.get('_index'))
                    # Load The API Roots Data
                    helpers.bulk(self.client, self.roots_data)

            # Prepare Status Data
            if not self.status_data:
                self.status_data = self.TAXXI_DEFAULT_STATUS
            for root in self.roots_data:
                if not self.client.indices.exists(f"{root.get('_id')}-status"):
                    log_info(f"Loading default data in status index: {root.get('_id')}-status")
                    # Create A Status Index Per Root
                    self.client.indices.create(index=f"{root.get('_id')}-status")
                    # Load The Status Data
                    helpers.bulk(self.client, self.status_data )

            # Prepare Collections Data
            if not self.collections_data:
                self.collections_data = self.TAXXI_DEFAULT_COLLECTIONS
            for root in self.roots_data:
                if not self.client.indices.exists(f"{root.get('_id')}-manifest"):
                    log_info(f"Loading default data in manifest index: {root.get('_id')}-manifest")
                    # Create A Manifest Index Per Root
                    self.client.indices.create(index=f"{root.get('_id')}-manifest")
                    # Load The Manifest Data Per Collection
                    for collection in self.collections_data:
                        if root.get('_id') in collection.get('_index'):
                            manifests = collection['_source'].get('manifest')
                            if manifests:
                                for manifest in manifests:
                                    manifest['collection'] = collection.get('_id')
                                    manifest_default = {
                                        "_index": f"{root.get('_id')}-manifest",
                                        "_source": manifest
                                    }
                                    manifests_data.append(manifest_default)
                    helpers.bulk(self.client, manifests_data)
                if not self.client.indices.exists(f"{root.get('_id')}-objects"):
                    log_info(f"Loading objects data in objects index: {root.get('_id')}-objects")
                    # Create An Objects Index Per Root
                    self.client.indices.create(index=f"{root.get('_id')}-objects")
                    # Load Objects Data Per Collection
                    for collection in self.collections_data:
                        if root.get('_id') in collection.get('_index'):
                            objects = collection['_source'].get('objects')
                            if objects:
                                for collection_object in objects:
                                    collection_object['collection'] = collection.get('_id')
                                    object_default = {
                                        "_index": f"{root.get('_id')}-objects",
                                        "_source": collection_object
                                    }
                                    objects_data.append(object_default)
                    helpers.bulk(self.client, objects_data)
            for root in self.roots_data:
                if not self.client.indices.exists(f"{root.get('_id')}-collections"):
                    log_info(f"Loading collections data in collections index: {root.get('_id')}-collections")
                    # Create A Collections Index Per Root
                    self.client.indices.create(index=f"{root.get('_id')}-collections")
                    # Load Collections Per Index
                    for collection in self.collections_data:
                        collection['_source'].pop("manifest", None)
                        collection['_source'].pop("responses", None)
                        collection['_source'].pop("objects", None)
                        collections.append(collection)
                    helpers.bulk(self.client, collections)

            # Create Next Index

            if not self.client.indices.exists('next'):
                log_info(f"Creating Next index...")
                # Create The API Roots Index
                self.client.indices.create('next')

        except Exception as error:
            log_error(error)

    def get_docs(self, index: str):
        try:
            res = self.client.search(index=index, size=10, sort='id')
            results = []
            for result in res['hits']['hits']:
                response = {}
                response.update(result['_source'])
                response.update({
                    'id': result['id']
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

    def scan(self, index: str, query_string: QueryString, sort_by: dict = None, fields: list = None):
        results = []
        search = Search(using=self.client, index=index).query(query_string).source(fields)
        scan_results = search.scan()

        for result in scan_results:
            results.append(result.to_dict())
        return {
            "more": False,
            "objects": results,
        }

    def search(self, index: str, query_string: QueryString, search_from: int, size: int,
               sort_by: dict = None, fields: list = None):
        results = []
        more = False
        search = Search(using=self.client, index=index).query(query_string).source(fields)[search_from:size]
        search = search.sort(sort_by)
        search_results = search.execute().to_dict()
        total = int(search_results['hits']['total']['value'])

        for result in search_results['hits']['hits']:
            response = {}
            response.update(result['_source'])
            results.append(response)

        if -1 < size < total :
            more = True

        return {
            "more": more,
            "objects": results,
        }

    def manifest_intersect(self, intersect_by: str,
                           objects_index: str, objects_query_string: QueryString,
                           manifests_index: str, manifests_query_string: QueryString,
                           version_range: Range = None, added_after_range: Range = None
                           ):
        objects_results = []
        objects_search = Search(using=self.client, index=objects_index).query(objects_query_string).source(intersect_by)
        objects_scan_results = objects_search.scan()
        for result in objects_scan_results:
            objects_results.append(result.to_dict()[intersect_by])

        manifests_results = []
        manifests_search = Search(using=self.client, index=manifests_index).query(manifests_query_string)\
            .source(intersect_by)
        if version_range:
            manifests_search = manifests_search.query(version_range)
        if added_after_range:
            manifests_search = manifests_search.query(added_after_range)
        manifests_scan_results = manifests_search.scan()
        for result in manifests_scan_results:
            manifests_results.append(result.to_dict()[intersect_by])

        objects_results_set = set(objects_results)
        intersections = objects_results_set.intersection(manifests_results)
        return intersections

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
