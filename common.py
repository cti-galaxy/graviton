import bisect
import copy
import datetime
import uuid
import operator
import pytz
import calendar
from elasticsearch_dsl.query import Range, Terms


def string_to_datetime(timestamp):
    try:
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


def get_version_field(stix_object):
    if "version" in stix_object:
        return stix_object["version"]
    elif "modified" in stix_object:
        return stix_object["modified"]
    elif "created" in stix_object:
        return stix_object["created"]
    else:
        return stix_object["date_added"]


def locate_version(stix_objects, locator):
    object_ids = []
    processed_objects = []
    for stix_object in stix_objects:
        position = bisect.bisect_left(object_ids, stix_object["id"])
        if not processed_objects or position >= len(object_ids) or object_ids[position] != stix_object["id"]:
            object_ids.insert(position, stix_object["id"])
            processed_objects.insert(position, stix_object)
        else:
            if locator(get_version_field(stix_object), get_version_field(processed_objects[position])):
                processed_objects[position] = stix_object
    return processed_objects


def check_for_dupes(final_objects, final_ids, matched_objects):
    for stix_object in matched_objects:
        found = 0
        position = bisect.bisect_left(final_ids, stix_object["id"])
        if not final_objects or position > len(final_ids) - 1 or final_ids[position] != stix_object["id"]:
            final_ids.insert(position, stix_object["id"])
            final_objects.insert(position, stix_object)
        else:
            stix_object_time = get_version_field(stix_object)
            while position != len(final_ids) and stix_object["id"] == final_ids[position]:
                if get_version_field(final_objects[position]) == stix_object_time:
                    found = 1
                    break
                else:
                    position = position + 1
            if found == 1:
                continue
            else:
                final_ids.insert(position, stix_object["id"])
                final_objects.insert(position, stix_object)


class Helper:

    @classmethod
    def fetch_objects_by_versions(cls, stix_objects, versions):
        final_objects = []
        final_ids = []

        if versions is None:
            versions = "last"
        if "all" in versions:
            return stix_objects

        versions = versions.split(",")
        specific_versions = []
        for version in versions:
            if version is not 'first' and version is not 'last':
                specific_versions.append(version)

        if specific_versions:
            object_ids = []
            matched_objects = []
            for stix_object in stix_objects:
                stix_object_version = get_version_field(stix_object)
                if stix_object_version in specific_versions:
                    position = bisect.bisect_left(object_ids, stix_object["id"])
                    object_ids.insert(position, stix_object["id"])
                    matched_objects.insert(position, stix_object)
            final_ids = object_ids
            final_objects = matched_objects

        if "first" in versions:
            matched_objects = locate_version(stix_objects, operator.lt)
            check_for_dupes(final_objects, final_ids, matched_objects)

        if "last" in versions:
            matched_objects = locate_version(stix_objects, operator.gt)
            check_for_dupes(final_objects, final_ids, matched_objects)

        return final_objects

    @classmethod
    def paginate(cls, pages_name, items, more=False, next_id=None):
        pages = {}
        if items:
            pages[pages_name] = items
        if pages_name == "objects" or pages_name == "versions":
            if next_id and pages:
                pages["next"] = next_id
            if pages:
                pages["more"] = more
        return pages

    @classmethod
    def determine_version(cls, new_obj, request_time):
        """Grab the modified time if present, if not grab created time,
        if not grab request time provided by server."""
        return new_obj.get("modified", new_obj.get("created", cls.datetime_to_string(request_time)))

    @classmethod
    def determine_spec_version(cls, obj):
        """Given a STIX 2.x object, determine its spec version."""
        missing = ("created", "modified")
        if all(x not in obj for x in missing):
            # Special case: only SCOs are 2.1 objects and they don't have a spec_version
            # For now the only way to identify one is checking the created and modified
            # are both missing.
            return "2.1"
        return obj.get("spec_version", "2.0")

    @classmethod
    def get_timestamp(cls):
        """Get current time with UTC offset"""
        return datetime.datetime.now(tz=pytz.UTC)

    @classmethod
    def skip_special_characters(cls, string):
        """Get current time with UTC offset"""
        return string.replace('-', '\\-')

    @classmethod
    def datetime_to_string(cls, dttm):
        """Given a datetime instance, produce the string representation
        with microsecond precision"""
        # 1. Convert to timezone-aware
        # 2. Convert to UTC
        # 3. Format in ISO format with microsecond precision

        if dttm.tzinfo is None or dttm.tzinfo.utcoffset(dttm) is None:
            # dttm is timezone-naive; assume UTC
            zoned = pytz.UTC.localize(dttm)
        else:
            zoned = dttm.astimezone(pytz.UTC)
        return zoned.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @classmethod
    def datetime_to_string_stix(cls, dttm):
        """Given a datetime instance, produce the string representation
        with millisecond precision"""
        # 1. Convert to timezone-aware
        # 2. Convert to UTC
        # 3. Format in ISO format with millisecond precision,
        #       except for objects defined with higher precision
        # 4. Add "Z"

        if dttm.tzinfo is None or dttm.tzinfo.utcoffset(dttm) is None:
            # dttm is timezone-naive; assume UTC
            zoned = pytz.UTC.localize(dttm)
        else:
            zoned = dttm.astimezone(pytz.UTC)
        ts = zoned.strftime("%Y-%m-%dT%H:%M:%S")
        ms = zoned.strftime("%f")
        if len(ms[3:].rstrip("0")) >= 1:
            ts = ts + "." + ms + "Z"
        else:
            ts = ts + "." + ms[:3] + "Z"
        return ts

    @classmethod
    def datetime_to_float(cls, dttm):
        """Given a datetime instance, return its representation as a float"""
        # Based on this solution: https://stackoverflow.com/questions/30020988/python3-datetime-timestamp-in-python2
        if dttm.tzinfo is None:
            return calendar.timegm(dttm.utctimetuple()) + dttm.microsecond / 1e6
        else:
            return (dttm - datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds()

    @classmethod
    def float_to_datetime(cls, timestamp_float):
        """Given a floating-point number, produce a datetime instance"""
        return datetime.datetime.utcfromtimestamp(timestamp_float)


    @classmethod
    def generate_status(
            cls, request_time, status, succeeded, failed, pending,
            successes=None, failures=None, pendings=None,
    ):
        """Generate Status Resource as defined in TAXII 2.1 section (4.3.1) <link here>`__."""
        status = {
            "id": str(uuid.uuid4()),
            "status": status,
            "request_timestamp": request_time,
            "total_count": succeeded + failed + pending,
            "success_count": succeeded,
            "failure_count": failed,
            "pending_count": pending,
        }

        if successes:
            status["successes"] = successes
        if failures:
            status["failures"] = failures
        if pendings:
            status["pendings"] = pendings
        return status

    @classmethod
    def generate_status_details(cls, id, version, message=None):
        """Generate Status Details as defined in TAXII 2.1 section (4.3.1) <link here>`__."""
        status_details = {
            "id": id,
            "version": version
        }

        if message:
            status_details["message"] = message

        return status_details

    @classmethod
    def get_custom_headers(cls, manifest_resource):
        """Generates the X-TAXII-Date-Added headers based on a manifest resource"""
        headers = {}

        times = sorted(map(lambda x: x["date_added"], manifest_resource.get("objects", [])))
        if len(times) > 0:
            headers["X-TAXII-Date-Added-First"] = times[0]
            headers["X-TAXII-Date-Added-Last"] = times[-1]

        return headers

    @classmethod
    def parse_request_parameters(cls, filter_args):
        """Generates a dict with params received from client"""
        session_args = {}
        for key, value in filter_args.items():
            if key != "limit" and key != "next":
                session_args[key] = set(value.replace(" ", "").split(","))
        return session_args

    @classmethod
    def find_att(cls, obj):
        """
        Used for finding the version attribute of an ambiguous object. Manifests
        use the "version" field, but objects will use "modified", or if that's not
        available, the "created" field.

        Args:
            obj (dict): manifest or stix object

        Returns:
            string value of the field from the object to use for versioning

        """
        if "version" in obj:
            return cls.string_to_datetime(obj["version"])
        elif "modified" in obj:
            return cls.string_to_datetime(obj["modified"])
        elif "created" in obj:
            return cls.string_to_datetime(obj["created"])
        else:
            return cls.string_to_datetime(obj["date_added"])

    @classmethod
    def find_version_attribute(cls, obj):
        if "modified" in obj:
            return "modified"
        elif "created" in obj:
            return "created"
        elif "date_added" in obj:
            return "date_added"

    @classmethod
    def check_for_dupes(cls, final_match, final_track, res):
        for obj in res:
            found = 0
            pos = bisect.bisect_left(final_track, obj["id"])
            if not final_match or pos > len(final_track) - 1 or final_track[pos] != obj["id"]:
                final_track.insert(pos, obj["id"])
                final_match.insert(pos, obj)
            else:
                obj_time = cls.find_att(obj)
                while pos != len(final_track) and obj["id"] == final_track[pos]:
                    if cls.find_att(final_match[pos]) == obj_time:
                        found = 1
                        break
                    else:
                        pos = pos + 1
                if found == 1:
                    continue
                else:
                    final_track.insert(pos, obj["id"])
                    final_match.insert(pos, obj)

    @classmethod
    def check_version(cls, data, relate):
        id_track = []
        res = []
        for obj in data:
            pos = bisect.bisect_left(id_track, obj["id"])
            if not res or pos >= len(id_track) or id_track[pos] != obj["id"]:
                id_track.insert(pos, obj["id"])
                res.insert(pos, obj)
            else:
                if relate(cls.find_att(obj), cls.find_att(res[pos])):
                    res[pos] = obj
        return res

    @classmethod
    def remove_hidden_field(cls, objs):
        for obj in objs:
            if "date_added" in obj:
                del obj["date_added"]

    @classmethod
    def find_added_headers(cls, headers, manifest, obj):
        obj_time = cls.find_att(obj)
        for man in manifest:
            if man["id"] == obj["id"] and obj_time == cls.find_att(man):
                if len(headers) == 0:
                    headers["X-TAXII-Date-Added-First"] = man["date_added"]
                else:
                    headers["X-TAXII-Date-Added-Last"] = man["date_added"]

    @classmethod
    def update_manifest(cls, new_obj, api_info, collection_id, request_time):
        collections = api_info.get("collections", [])
        media_type_fmt = "application/stix+json;version={}"

        for collection in collections:
            if collection_id == collection["id"]:
                version = cls.determine_version(new_obj, request_time)
                request_time = cls.datetime_to_string(request_time)
                media_type = media_type_fmt.format(cls.determine_spec_version(new_obj))

                # version is a single value now, therefore a new manifest is always created
                collection["manifest"].append(
                    {
                        "id": new_obj["id"],
                        "date_added": request_time,
                        "version": version,
                        "media_type": media_type,
                    },
                )

                # if the media type is new, attach it to the collection
                if media_type not in collection["media_types"]:
                    collection["media_types"].append(media_type)

                # quit once you have found the collection that needed updating
                break


class Filter:

    def __init__(self, filter_args):
        self.filter_args = filter_args

    def sort_and_paginate(self, data, limit, manifest):
        temp = None
        next_save = {}
        headers = {}
        new = []
        if len(data) == 0:
            return new, next_save, headers
        if manifest:
            manifest.sort(key=lambda x: x['date_added'])
            for man in manifest:
                man_time = Helper.find_att(man)
                for check in data:
                    check_time = Helper.find_att(check)
                    if check['id'] == man['id'] and check_time == man_time:
                        if len(headers) == 0:
                            headers["X-TAXII-Date-Added-First"] = man["date_added"]
                        new.append(check)
                        temp = man
                        if len(new) == limit:
                            headers["X-TAXII-Date-Added-Last"] = man["date_added"]
                        break
            if limit and limit < len(data):
                next_save = new[limit:]
                new = new[:limit]
            else:
                headers["X-TAXII-Date-Added-Last"] = temp["date_added"]
        else:
            data.sort(key=lambda x: x['date_added'])
            if limit and limit < len(data):
                next_save = data[limit:]
                data = data[:limit]
            headers["X-TAXII-Date-Added-First"] = data[0]["date_added"]
            headers["X-TAXII-Date-Added-Last"] = data[-1]["date_added"]
            new = data
        return new, next_save, headers

    @staticmethod
    def filter_by_id(data, id_):
        id_ = id_.split(",")

        match_objects = []

        for obj in data:
            if "id" in obj and any(s == obj["id"] for s in id_):
                match_objects.append(obj)

        return match_objects

    def filter_by_added_after(self, data, manifest_info, added_after_date):
        added_after_timestamp = string_to_datetime()
        new_results = []
        # for manifest objects and versions
        if manifest_info is None:
            for obj in data:
                if string_to_datetime() > added_after_timestamp:
                    new_results.append(obj)
        # for other objects with manifests
        else:
            for obj in data:
                obj_time = Helper.find_att(obj)
                for item in manifest_info:
                    item_time = Helper.find_att(item)
                    if item["id"] == obj["id"] and item_time == obj_time and \
                            string_to_datetime() > added_after_timestamp:
                        new_results.append(obj)
                        break
        return new_results

    def filter_by_version(self, data, version):
        # final_match is a sorted list of objects
        final_match = []
        # final_track is a sorted list of id's
        final_track = []

        # return most recent object versions unless otherwise specified
        if version is None:
            version = "last"
        version_indicators = version.split(",")

        if "all" in version_indicators:
            # if "all" is in the list, just return everything
            return data

        actual_dates = [string_to_datetime() for x in version_indicators if x != "first" and x != "last"]
        # if a specific version is given, filter for objects with that value
        if actual_dates:
            id_track = []
            res = []
            for obj in data:
                obj_time = Helper.find_att(obj)
                if obj_time in actual_dates:
                    pos = bisect.bisect_left(id_track, obj["id"])
                    id_track.insert(pos, obj["id"])
                    res.insert(pos, obj)
            final_match = res
            final_track = id_track

        if "first" in version_indicators:
            res = Helper.check_version(data, operator.lt)
            Helper.check_for_dupes(final_match, final_track, res)

        if "last" in version_indicators:
            res = Helper.check_version(data, operator.gt)
            Helper.check_for_dupes(final_match, final_track, res)

        return final_match

    def filter_by_type(self, data, type_):
        type_ = type_.split(",")
        match_objects = []

        for obj in data:
            if "type" in obj and any(s == obj["type"] for s in type_):
                match_objects.append(obj)
            elif "id" in obj and any(s == obj["id"].split("--")[0] for s in type_):
                match_objects.append(obj)

        return match_objects

    def filter_by_spec_version(self, data, spec_):
        match_objects = []

        if spec_:
            spec_ = spec_.split(",")
            for obj in data:
                if "media_type" in obj:
                    if any(s == obj["media_type"].split("version=")[1] for s in spec_):
                        match_objects.append(obj)
                elif any(s == Helper.determine_spec_version(obj) for s in spec_):
                    match_objects.append(obj)
        else:
            for obj in data:
                add = True
                if "media_type" in obj:
                    s1 = obj["media_type"].split("version=")[1]
                else:
                    s1 = Helper.determine_spec_version(obj)
                for match in data:
                    if "media_type" in match:
                        s2 = match["media_type"].split("version=")[1]
                    else:
                        s2 = Helper.determine_spec_version(match)
                    if obj["id"] == match["id"] and s2 > s1:
                        add = False
                if add:
                    match_objects.append(obj)
        return match_objects

    def process_filter(self, data, allowed=(), manifest_info=(), limit=None):
        filtered_by_type = []
        filtered_by_id = []
        filtered_by_spec_version = []
        filtered_by_added_after = []
        filtered_by_version = []
        final_match = []
        save_next = []
        headers = {}

        # match for type and id filters first
        match_type = self.filter_args.get("match[type]")
        if match_type and "type" in allowed:
            filtered_by_type = self.filter_by_type(data, match_type)
        else:
            filtered_by_type = copy.deepcopy(data)

        match_id = self.filter_args.get("match[id]")
        if match_id and "id" in allowed:
            filtered_by_id = self.filter_by_id(filtered_by_type, match_id)
        else:
            filtered_by_id = filtered_by_type

        # match for added_after
        added_after_date = self.filter_args.get("added_after")
        if added_after_date:
            filtered_by_added_after = self.filter_by_added_after(filtered_by_id, manifest_info, added_after_date)
        else:
            filtered_by_added_after = filtered_by_id

        # match for spec_version
        match_spec_version = self.filter_args.get("match[spec_version]")
        if "spec_version" in allowed:
            filtered_by_spec_version = self.filter_by_spec_version(filtered_by_added_after, match_spec_version)
        else:
            filtered_by_spec_version = filtered_by_added_after

        # match for version, and get rid of duplicates as appropriate
        if "version" in allowed:
            match_version = self.filter_args.get("match[version]")
            filtered_by_version = self.filter_by_version(filtered_by_spec_version, match_version)
        else:
            filtered_by_version = filtered_by_spec_version

        # sort objects by date_added of manifest and paginate as necessary
        final_match, save_next, headers = self.sort_and_paginate(filtered_by_version, limit, manifest_info)

        return final_match, save_next, headers

    @staticmethod
    def get_total_results(response_dict):
        total_results = response_dict.get('hits', {}).get('total')
        if not str(total_results).isdigit():
            total_results = total_results.get('value')
            total_dict = response_dict.get('hits').get('total')
        else:
            total_dict = {
                'value': total_results,
            }
        return total_dict, total_results


class Pagination:

    def __init__(self, **kwargs):
        self.next = {}

    def set_next(self, objects, args):
        u = str(uuid.uuid4())
        if "limit" in args:
            del args["limit"]
        for arg in args:
            new_list = args[arg].split(',')
            new_list.sort()
            args[arg] = new_list
        d = {"objects": objects, "args": args, "request_time": Helper.datetime_to_float(Helper.get_timestamp())}
        self.next[u] = d
        return u

    def get_next(self, filter_args, manifest, lim):
        n = filter_args["next"]
        if n in self.next:
            for arg in filter_args:
                new_list = filter_args[arg].split(',')
                new_list.sort()
                filter_args[arg] = new_list
            del filter_args["next"]
            del filter_args["limit"]
            if filter_args != self.next[n]["args"]:
                raise Exception("The server did not understand the request or filter parameters: "
                                "params changed over subsequent transaction", 400)
            t = self.next[n]["objects"]
            length = len(self.next[n]["objects"])
            headers = {}
            ret = []
            if length <= lim:
                limit = length
                more = False
                nex = None
            else:
                limit = lim
                more = True

            for i in range(0, limit):
                x = t.pop(0)
                ret.append(x)
                if len(headers) == 0:
                    Helper.find_added_headers(headers, manifest, x)
                if i == limit - 1:
                    Helper.find_added_headers(headers, manifest, x)
            if not more:
                self.next.pop(n)
            else:
                nex = n

            return ret, more, headers, nex
        else:
            raise Exception("The server did not understand the request or filter parameters: 'next' not valid", 400)
