import time
import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import QueryString
from .common import Helper, Filter, Pagination
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
    if json.load(open('config/constants.json', encoding="utf8")).get('maximum_page_size'):
        PAGE_SIZE: int = int(json.load(open('config/constants.json', encoding="utf8")).get('maximum_page_size'))
    else:
        PAGE_SIZE: int = 10

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
        self.max_page_size = self.PAGE_SIZE

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
                                        "_id": manifest['id'],
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
                                        "_id": collection_object['id'],
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

    def search_manifests(self, index: str, query_parameters: dict = None):
        size = int(query_parameters.get('limit'))
        added_after = query_parameters.get('added_after')
        types = query_parameters.get('types')
        ids = query_parameters.get('ids')
        versions = query_parameters.get('versions')
        spec_versions = query_parameters.get('spec_versions')
        base_page = 0
        more = False
        next_id = 0

        if query_parameters is None:
            query_parameters = {}

        if query_parameters.get('next'):
            next_objects = self.client.get(index='next', id=query_parameters.get('next'))
            if not next_objects:
                raise es_exceptions.NotFoundError
        try:
            objects = []
            manifests = []

            # Query Objects by collection id, types and spec_versions
            objects_query = f"collection : {query_parameters.get('collection_id')}"
            if types:
                types = types.replace(",", " OR ")
                objects_query = objects_query + f" AND type : ('{types}')"
            if spec_versions:
                spec_versions = spec_versions.replace(",", " OR ")
                objects_query = objects_query + f" AND spec_version : ('{spec_versions}')"
            query_string = QueryString(query=objects_query, default_operator="and")
            search = Search(using=self.client, index=f'{index}-objects').query(query_string)
            results = search.execute().to_dict()['hits']['hits']
            for result in results:
                objects.append(result['_id'])

            # Query Manifests by collection id, object id and versions
            manifest_query = f"collection : {query_parameters.get('collection_id')}"
            if ids:
                ids = ids.replace(",", " OR ")
                manifest_query = manifest_query + f" AND id : ('{ids}')"
            if versions:
                versions = versions.replace(",", " OR ")
                manifest_query = manifest_query + f" AND version : '2020-01-20T00:00:00.000Z'"
                print (manifest_query)
            query_string = QueryString(query=manifest_query, default_operator="and")
            search = Search(using=self.client, index=f'{index}-manifest').query(query_string)
            results = search.execute().to_dict()['hits']['hits']
            for result in results:
                manifests.append(result['_id'])

            # Intersect the results of Object and Minfest queries and output a list of object id's
            objects_set = set(objects)
            matched_ids = objects_set.intersection(manifests)

            if matched_ids:
                # Execute the manifest Search

                matched_ids = ",".join(matched_ids).replace(',', ' OR ')
                query_string = QueryString(query=f"id:('{matched_ids}')", default_operator="AND")

                if -1 < size < self.max_page_size:
                    search = Search(using=self.client, index=f'{index}-manifest').query(query_string)[base_page:base_page +
                                                                                        size]
                else:
                    search = Search(using=self.client, index=f'{index}-manifest').query(query_string)[base_page:base_page +
                                                                                        self.max_page_size]
                search = search.sort({'date_added': {'order': 'asc'}})
                search_results = search.execute().to_dict()
                total = int(search_results['hits']['total']['value'])

                results = []
                for result in search_results['hits']['hits']:
                    response = {}
                    response.update(result['_source'])
                    response.update({
                        'id': result['_id']
                    })
                    results.append(response)
                if -1 < size < total or total > self.max_page_size:
                    more = True
            else:
                results = []

            return {
                "more": more,
                "objects": results,
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
