# -*- coding: utf-8 -*-
# Copyright 2013 UNED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.contrib.auth.models import User
from django.db import connection, models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from moocng.courses.models import Announcement

from moocng.mongodb import get_micro_blog_db
import pymongo
from dateutil import tz
from datetime import date, datetime
from bson.objectid import ObjectId

class Organization(models.Model):
    name = models.CharField(verbose_name=_(u"Organization name"),
                                    max_length=256)
    logo = models.ImageField(upload_to="organizations",
                            # height_field=256,
                            # width_field=256,
                            verbose_name=_(u"Organization logo"),
                            max_length=256)

    def __unicode__(self):
        return unicode(self.name)


class UserProfile(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    last_announcement = models.ForeignKey(Announcement,
                                          verbose_name=_('Last announcement viewed'),
                                          null=True,
                                          blank=True)

    organization = models.ManyToManyField(Organization, verbose_name=_(u'Organization'),
                                                        null=True)
    GENDER_CHOICES = (
        ('m', _(u'Male')),
        ('f', _(u'Female'))
    )
    gender = models.CharField(verbose_name=_(u"Gender"),
                                    max_length=1,
                                    choices=GENDER_CHOICES,
                                    null=True,
                                    blank=True)
    personalweb = models.CharField(verbose_name=_(u"Personal website"),
                                    max_length=256,
                                    null=True,
                                    blank=True)
    birthdate = models.DateField(verbose_name=_(u"Birthdate"),
                                    null=True)
    bio = models.TextField(verbose_name=_(u"Biography"),
                                    null=True,
                                    blank=True)
    karma = models.IntegerField(verbose_name=_(u"Karma"),
                                    default=0)
    

    class Meta:
        verbose_name = _('User profile')
        verbose_name_plural = _('User profiles')

    def __unicode__(self):
        return unicode(self.user)

@receiver(signals.post_save, sender=User, dispatch_uid="create_user_profile")
def create_user_profile(sender, instance, created, **kwargs):
    tables = connection.introspection.table_names()
    try:
        profile = instance.get_profile()
    except UserProfile.DoesNotExist:
        profile = None
    if not profile and UserProfile._meta.db_table in tables:
        UserProfile.objects.create(user=instance)


def get_blog_user(id):
    return get_micro_blog_db().get_collection('user').find_one({'id_user': id})

def update_following_blog_user(id, following):
    get_micro_blog_db().get_collection('user').update({"id_user": id}, {"$set": {"following": following}})

def insert_blog_user(user):
    get_micro_blog_db().get_collection('user').insert(user)

def get_posts(case, id, user, page):
    postCollection = get_micro_blog_db().get_collection('post')
    idsUsers=[{"id_user": id}]
    if(case == 0 and user):
        for following in user["following"]:
                idsUsers.append({"id_user": following})
        
    posts = postCollection.find({"$or": idsUsers})[page:page+10].sort("date",pymongo.DESCENDING)

    return _processPost(posts)

def insert_post(post):
    get_micro_blog_db().get_collection('post').insert(post)

def count_posts(id):
    return get_micro_blog_db().get_collection('post').find({'id_user': id}).count()

def _processPost(posts):
    listPost = []
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    for post in posts:
        # post["text"] = post["text"]
        # post["email"] = "@" + post["email"].split("@")[0]
        post["date"] = datetime.strptime(post.get("date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
        if("original_date" in post):
            post["original_date"] = datetime.strptime(post.get("original_date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
        post["id"] = post.pop("_id")
        listPost.append(post)

    return listPost

def save_retweet(request, id):
    postCollection = get_micro_blog_db().get_collection('post')
    post = postCollection.find_one({"$and": [{"id_user":request.user.id},{"id_original_post":ObjectId(id)}]})

    if(not post):
        postCollection.update({"$or": [{"_id": ObjectId(id)}, {"id_original_post": ObjectId(id)}]}, {"$inc": {"shared":  1}}, multi=True)
        post = postCollection.find_one({"_id": ObjectId(id)})
        post["id_user"] = request.user.id
        post["id_original_post"] = post["_id"]
        post["original_date"] = post["date"]
        post["date"] = datetime.utcnow().isoformat()
        post["shared_by"] = "@" + request.user.username
        del post["_id"]
        insert_post(post)
        return True

    return False

def get_num_followers(id):
    return get_micro_blog_db().get_collection('user').find({"following": {"$eq" : id}}).count()

