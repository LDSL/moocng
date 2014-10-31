from django.conf import settings
from django.contrib.messages import success
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from moocng.courses.security import (get_course_if_user_can_view_or_404,
                                    get_course_if_user_can_view_and_permission)
from moocng.enrollment.idp import enroll_course_at_idp
from moocng import mongodb
from bson.objectid import ObjectId
import pymongo

def free_enrollment(request, course_slug):
    course, permission = get_course_if_user_can_view_and_permission(course_slug, request)
    if permission:
        if request.method == 'POST':

            groupCollection = mongodb.get_db().get_collection('groups')
            groups = groupCollection.find({ 'id_course': course.id}).sort("size",pymongo.ASCENDING)
            if(groups and groups.count() > 0):
                group = groups[0]
                new_member =    {"id_user": request.user.id, "username": request.user.username, 
                                "first_name":request.user.first_name, "last_name":request.user.last_name, 
                                "email": request.user.email, "karma": request.user.get_profile().karma, "countries": "", 
                                "languages": ""}

                if(len(group["members"]) <= course.group_max_size + (course.group_max_size * 0.5)):
                    group["size"] += 1
                    group["members"].append(new_member)

                    groupCollection.update({'_id': ObjectId(group["_id"])}, {"$set": {"members": group["members"], "size": group["size"]}})

                else:
                    group = {"id_course": course.id, "name": "Group" + str(groups.count()+1), "size": 1, "members": []}
                    group["members"].append(new_member)
                    groupCollection.insert(group)
           
            user = request.user
            old_course_status = 'f'
            if course.created_from:
                if course.created_from.students.filter(pk=user.pk):
                    old_course_status = 'n'
            course.students.through.objects.create(student=user,
                                                   course=course,
                                                   old_course_status=old_course_status)
            if getattr(settings, 'FREE_ENROLLMENT_CONSISTENT', False):
                enroll_course_at_idp(request.user, course)
            success(request,
                    _(u'Congratulations, you have successfully enroll in the course %(course)s')
                    % {'course': unicode(course)})

    return HttpResponseRedirect(reverse('course_overview',
                                        args=(course.slug, )))


def free_unenrollment(request, course_slug):
    course, permission = get_course_if_user_can_view_and_permission(course_slug, request)
    if request.method == 'POST':

        groupCollection = mongodb.get_db().get_collection('groups')
        group = groupCollection.find_one( { 'id_course': course.id, 'members.id_user':request.user.id } )
        if(group):
            for m in group["members"]:
                if(m["id_user"] == request.user.id):
                    group["members"].remove(m)
                    group["size"] -= 1

            groupCollection.update({'_id': ObjectId(group["_id"])}, {"$set": {"members": group["members"], "size": group["size"]}})

        user = request.user
        course.students.through.objects.get(student=user,
                                            course=course).delete()
        success(request,
                _(u'You have successfully unenroll in the course %(course)s')
                % {'course': unicode(course)})

        

    return HttpResponseRedirect(reverse('course_overview',
                                        args=(course.slug, )))
