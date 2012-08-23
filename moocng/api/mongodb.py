import bson

import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pymongo.connection import Connection

from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import Resource


class MongoObj(object):

    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if hasattr(initial, 'items'):
            self.__dict__['_data'] = initial

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data


class MongoResource(Resource):

    collection = None  # subclasses should implement this

    def __init__(self, *args, **kwargs):
        super(MongoResource, self).__init__(*args, **kwargs)

        try:
            db_uri = settings.MONGODB_URI
        except AttributeError:
            raise ImproperlyConfigured('Missing required MONGODB_URI setting')

        uri_parts = urlparse.urlparse(db_uri)

        if uri_parts.path:
            database_name = uri_parts.path[1:]
        else:
            try:
                database_name = settings.MONGODB_NAME
            except AttributeError:
                raise ImproperlyConfigured('You did not supply the database name in MONGODB_URI neither in MONGODB_NAME')


        self._connection = Connection(db_uri)
        self._database = self._connection[database_name]
        self._collection = self._database[self.collection]

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {'resource_name': self._meta.resource_name}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = str(bundle_or_obj.obj._id)
        else:
            kwargs['pk'] = str(bundle_or_obj._id)

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url('api_dispatch_detail', kwargs=kwargs)

    def get_object_list(self, request):
        results = []
        for result in self._collection.find():
            obj = MongoObj(initial=result)
            obj.uuid = str(result['_id'])
            results.append(obj)

        return results

    def obj_get_list(self, request=None, **kwargs):
        # no filtering by now
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        bid = bson.ObjectId(kwargs['pk'])
        result = self._collection.find_one({'_id': bid})
        if result is None:
            raise NotFound('Invalid resource lookup data provided')

        obj = MongoObj(initial=result)
        obj.uuid = str(result['_id'])
        return obj

    def obj_create(self, bundle, request=None, **kwargs):
        bundle = self.full_hydrate(bundle)
        bundle.obj = MongoObj(bundle.data)
        _id = self._collection.insert(bundle.data, safe=True)
        bundle.obj.uuid = str(_id)
        return bundle

