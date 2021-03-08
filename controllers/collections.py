import json
from middleware.logging import log_debug, log_info, log_error
from services.esdb import EsClient
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import QueryString, Range, Terms
from common import Helper

EXCEPTIONS: dict = json.load(open('config/schema/exceptions.json', encoding="utf8"))

if json.load(open('config/constants.json', encoding="utf8")).get('maximum_page_size'):
    PAGE_SIZE: int = int(json.load(open('config/constants.json', encoding="utf8")).get('maximum_page_size'))
else:
    PAGE_SIZE: int = 10


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
        objects_query = None
        manifest_query = None
        version_range = None
        added_after_range = None
        size = int(query_parameters.get('limit'))
        max_page_size = PAGE_SIZE
        added_after = query_parameters.get('added_after')
        sort_by = {'date_added': {'order': 'asc'}}
        types = query_parameters.get('types')
        ids = query_parameters.get('ids')
        versions = query_parameters.get('versions')
        spec_versions = query_parameters.get('spec_versions')
        base_page = 0
        next_id = 0
        objects_query = None
        manifest_query = None
        version_range = None
        added_after_range = None

        log_debug(f"Request to Get The objects Manifest of Collection: {query_parameters.get('collection_id')} "
                  f"in the Feed Root: {api_root}")

        if query_parameters is None:
            query_parameters = {}

        try:
            # Create a Query to filter Objects by collection id, types and spec_versions
            objects_query = f"collection : {query_parameters.get('collection_id')}"
            if types:
                types = types.replace(",", " OR ")
                objects_query = objects_query + f" AND type : ('{types}')"
            if spec_versions:
                spec_versions = spec_versions.replace(",", " OR ")
                objects_query = objects_query + f" AND spec_version : ('{spec_versions}')"
            objects_query_string = QueryString(query=objects_query, default_operator="and")

            # Create a Query to filter Manifest by collection id, object id's, versions and added after dates
            manifest_query = f"collection : {query_parameters.get('collection_id')}"
            if ids:
                ids = ids.replace(",", " OR ")
                manifest_query = manifest_query + f" AND id : ('{ids}')"
            if added_after:
                added_after_range = Range(**{'date_added': {'gt': f'{added_after}'}})
            manifests_query_string = QueryString(query=manifest_query, default_operator="and")

            # Get the intersect of both Objects and Manifest Queries
            intersected_results = cls.es_client.manifest_intersect(
                intersect_by='id',
                objects_index=f'{api_root}-objects', objects_query_string=objects_query_string,
                manifests_index=f'{api_root}-manifest', manifests_query_string=manifests_query_string,
                version_range=version_range, added_after_range=added_after_range
            )

            # Version and Paginate The Results
            if intersected_results:
                manifest_ids = ",".join(intersected_results).replace(',', ' OR ')
                query_string = QueryString(query=f"id:('{manifest_ids}')", default_operator="AND")
                pre_versioning_results = cls.es_client.scan(index=f'{api_root}-manifest', query_string=query_string)
                pre_pagination_results = Helper.match_version(stix_data=pre_versioning_results,versions=versions)
                if -1 < size < max_page_size:
                    results = cls.es_client.search(index=f'{api_root}-manifest', query_string=query_string,
                                                   search_from=base_page, size=size, sort_by=sort_by)
                else:
                    results = cls.es_client.search(index=f'{api_root}-manifest', query_string=query_string,
                                                   search_from=base_page, size=max_page_size, sort_by=sort_by)
            else:
                results = {
                    "objects": []
                }
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
