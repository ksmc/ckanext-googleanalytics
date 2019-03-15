import logging
from ckan.lib.base import BaseController, c, render, request
import dbutil

import urllib
import urllib2

import logging
import ckan.logic as logic
import hashlib
import plugin
from pylons import config
import paste.deploy.converters as converters

from webob.multidict import UnicodeMultiDict
from paste.util.multidict import MultiDict

from ckan.controllers.api import ApiController
import ckan.model as model

log = logging.getLogger('ckanext.googleanalytics')

class GAController(BaseController):
    def view(self):
        # get package objects corresponding to popular GA content
        c.top_resources = dbutil.get_top_resources(limit=10)
        return render('summary.html')

class GAApiController(ApiController):
    # intercept API calls to record via google analytics
    def _post_analytics(
            self, user, request_obj_type, request_function, request_id):
        if config.get('googleanalytics.id'):
            data_dict = {
                "v": 1, 
                "tid": config.get('googleanalytics.id'),
                "cid": hashlib.md5(user).hexdigest(),
                # customer id should be obfuscated
                "t": "event",
                "dh": c.environ['HTTP_HOST'],
                "dp": c.environ['PATH_INFO'],
                "dr": c.environ.get('HTTP_REFERER', ''),
                "ec": "CKAN API Request",
                "ea": request_obj_type+request_function,
                "el": request_id,
            }
            try:
               if converters.asbool(config.get('googleanalytics.activities_tracker', False)) == True:
                    context = {'model': model, 'session': model.Session, 'user': c.user}
                    data = {
                                'el': request_id,
                                'ec': "CKAN API Request",
                                'ea': "-".join([request_obj_type,request_function]),
                            }    
                    logic.get_action('resource_tracker_create')(context, data)
            except:
                pass
            plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)

    def action(self, logic_function, ver=None):
        try:
            function = logic.get_action(logic_function)
            side_effect_free = getattr(function, 'side_effect_free', False)
            request_data = self._get_request_data(
                try_url_params=side_effect_free)
            if isinstance(request_data, dict):
                id = request_data.get('id', '')
                if 'q' in request_data:
                    id = request_data['q']
                if 'query' in request_data:
                    id = request_data['query']
                self._post_analytics(c.user, logic_function, '', id)
        except Exception, e:
            log.debug(e)
            pass

        return ApiController.action(self, logic_function, ver)

    def list(self, ver=None, register=None,
             subregister=None, id=None):
        self._post_analytics(c.user,
                             register +
                             ("_"+str(subregister) if subregister else ""),
                             "list",
                             id)
        return ApiController.list(self, ver, register, subregister, id)

    def show(self, ver=None, register=None,
             subregister=None, id=None, id2=None):
        self._post_analytics(c.user,
                             register +
                             ("_"+str(subregister) if subregister else ""),
                             "show",
                             id)
        return ApiController.show(self, ver, register, subregister, id, id2)

    def update(self, ver=None, register=None,
               subregister=None, id=None, id2=None):
        self._post_analytics(c.user,
                             register +
                             ("_"+str(subregister) if subregister else ""),
                             "update",
                             id)
        return ApiController.update(self, ver, register, subregister, id, id2)

    def delete(self, ver=None, register=None,
               subregister=None, id=None, id2=None):
        self._post_analytics(c.user,
                             register +
                             ("_"+str(subregister) if subregister else ""),
                             "delete",
                             id)
        return ApiController.delete(self, ver, register, subregister, id, id2)

    def search(self, ver=None, register=None):
        id = None
        try:
            params = MultiDict(self._get_search_params(request.params))
            if 'q' in params.keys():
                id = params['q']
            if 'query' in params.keys():
                id = params['query']
        except ValueError, e:
            log.debug(str(e))
            pass
        self._post_analytics(c.user, register, "search", id)

        return ApiController.search(self, ver, register)

# from ckanext.datastore.controller import DatastoreController
# class GADatastoreController(DatastoreController):
#     # intercept datastore dump calls to record via google analytics
#     def _post_analytics(
#             self, user, request_obj_type, request_function, request_id):
#         if config.get('googleanalytics.id'):
#             data_dict = {
#                 "v": 1,
#                 "tid": config.get('googleanalytics.id'),
#                 "cid": hashlib.md5(user).hexdigest(),
#                 # customer id should be obfuscated
#                 "t": "event",
#                 "dh": c.environ['HTTP_HOST'],
#                 "dp": c.environ['PATH_INFO'],
#                 "dr": c.environ.get('HTTP_REFERER', ''),
#                 "ec": "CKAN DataStore Download",
#                 "ea": request_obj_type+request_function,
#                 "el": request_id,
#             }
#             try:
#                if converters.asbool(config.get('googleanalytics.activities_tracker', False)) == True:
#                     context = {'model': model, 'session': model.Session, 'user': c.user}
#                     data = {
#                                 'resource_id': request_id,
#                                 'event': request_function,
#                                 'obj_type': request_obj_type,
#                             }    
#                     logic.get_action('resource_tracker_create')(context, data)
#             except:
#                 pass
#             plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)
#     
#     def dump(self, resource_id):
#         data, errors = dict_fns.validate(dict(request.GET), dump_schema())
#         if errors:
#             abort(400, u'\n'.join(
#                 u'{0}: {1}'.format(k, ' '.join(e)) for k, e in errors.items()))
# 
#         try:
#             dump_to(
#                 resource_id,
#                 response,
#                 fmt=data['format'],
#                 offset=data['offset'],
#                 limit=data.get('limit'),
#                 options={u'bom': data['bom']},
#                 sort=data['sort'],
#                 search_params={
#                     k: v for k, v in data.items() if k in [
#                         'filters',
#                         'q',
#                         'distinct',
#                         'plain',
#                         'language',
#                         'fields']},
#                 )
#             self._post_analytics(c.user, 'Datastore', 'Download', resource_id)
#         except ObjectNotFound:
#             abort(404, _('DataStore resource not found'))