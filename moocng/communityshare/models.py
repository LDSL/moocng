from django.db import models
from django.core.urlresolvers import reverse

import pymongo
import re
from dateutil import tz
from datetime import date, datetime

from moocng.mongodb import get_db
from bson.objectid import ObjectId

class CommunityShareBase(object):
	def __init__(self, prefix='share'):
		self.col_prefix=prefix
		self.col_user = '%s_user' % self.col_prefix
		self.col_post = '%s_post' % self.col_prefix

	def get_blog_user(self, id):
	    return get_db().get_collection(self.col_user).find_one({'id_user': id})

	def insert_blog_user(self, user):
	    get_db().get_collection(self.col_user).insert(user)

	def get_posts(self, case, id, user, page):
	    postCollection = get_db().get_collection(self.col_post)
	    idsUsers=[{"id_user": id}]
	    if(case == 0 and user):
	        for following in user["following"]:
	                idsUsers.append({"id_user": following})
	        
	    posts = postCollection.find({"$and": [{"$or": idsUsers, }, {"$or": [ {"is_child": {"$exists": False} }, {"is_child": False} ] } ] })[page:page+10].sort("date",pymongo.DESCENDING)
	    posts_list = []
	    for post in posts:
	        if len(post['children']) > 0:
	            self._proccess_post_children(post)
	        posts_list.append(post)

	    return self._processPostList(posts_list)

	def search_posts(self, query, page):
	    postCollection = get_db().get_collection(self.col_post)
	    mongoQuery = {'$regex': '.*%s.*' % (query)}

	    posts = postCollection.find({'text': mongoQuery})[page:page+10].sort("date",pymongo.DESCENDING)

	    return self._processPostList(posts)

	def insert_post(self, post):
	    get_db().get_collection(self.col_post).insert(post)

	def count_posts(self, id):
	    return get_db().get_collection(self.col_post).find({'id_user': id}).count()

	def _hashtag_to_link(self, matchobj):
	    hashtag = matchobj.group(0)
	    hashtagUrl = reverse('profile_posts_hashtag', args=[hashtag[1:]])
	    return '<a href="%s">%s</a>' % (hashtagUrl, hashtag)

	def _proccess_hashtags(self, text):
	    hashtagged = re.sub(r'(?:(?<=\s)|^)#(\w*[A-Za-z_]+\w*)', self._hashtag_to_link, text)
	    return hashtagged

	def _processPost(post, from_zone, to_zone):
	    post["date"] = datetime.strptime(post.get("date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	    if("original_date" in post):
	        post["original_date"] = datetime.strptime(post.get("original_date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	    post["id"] = post.pop("_id")
	    post["text"] = _proccess_hashtags(post["text"])
	    listPost.append(post)

	def _processPostList(self, posts):
	    listPost = []
	    from_zone = tz.tzutc()
	    to_zone = tz.tzlocal()

	    for post in posts:
	        post["date"] = datetime.strptime(post.get("date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	        if("original_date" in post):
	            post["original_date"] = datetime.strptime(post.get("original_date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	        post["id"] = post.pop("_id")
	        post["text"] = self._proccess_hashtags(post["text"])
	        listPost.append(post)

	    return listPost

	def _proccess_post_children(self, post):
	    postCollection = get_db().get_collection(self.col_post)
	    from_zone = tz.tzutc()
	    to_zone = tz.tzlocal()
	    post['replies'] = []
	    for child in post['children']:
	        post_child = postCollection.find({'_id': child}).limit(1)[0]
	        if post_child and len(post_child['children']) > 0:
	            self._proccess_post_children(post_child)

	        post_child["date"] = datetime.strptime(post_child.get("date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	        if("original_date" in post_child):
	            post_child["original_date"] = datetime.strptime(post_child.get("original_date"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=from_zone).astimezone(to_zone).strftime('%d %b %Y').upper()
	        post_child["id"] = post_child.pop("_id")
	        post_child["text"] = self._proccess_hashtags(post_child["text"])

	        post['replies'].append(post_child)

	def save_reply(self, request, id, post):
	    postCollection = get_db().get_collection(self.col_post)
	    post_orig = postCollection.find_one({"_id":ObjectId(id)})
	    if post_orig:
	        post['is_child'] = True
	        reply_id = postCollection.insert(post)
	        post_orig["children"].append(reply_id)
	        postCollection.update({'_id': ObjectId(id)}, {"$set": {"children": post_orig["children"]}})
	        return True
	    else:
	        return False

class Microblog(CommunityShareBase):
	def __init__(self):
		super(Microblog,self).__init__('microblog')

	def get_num_followers(self, id):
	    return get_db().get_collection(self.col_user).find({"following": {"$eq" : id}}).count()

	def update_following_blog_user(self, id, following):
	    get_db().get_collection(self.col_user).update({"id_user": id}, {"$set": {"following": following}})

	def save_retweet(self, request, id):
	    postCollection = get_db().get_collection(self.col_post)
	    post = postCollection.find_one({"$and": [{"id_user":request.user.id},{"id_original_post":ObjectId(id)}]})

	    if(not post):
	        postCollection.update({"$or": [{"_id": ObjectId(id)}, {"id_original_post": ObjectId(id)}]}, {"$inc": {"shared":  1}}, multi=True)
	        post = postCollection.find_one({"_id": ObjectId(id)})
	        post["id_author"] = post["id_user"]
	        post["id_user"] = request.user.id
	        post["id_original_post"] = post["_id"]
	        post["original_date"] = post["date"]
	        post["date"] = datetime.utcnow().isoformat()
	        post["shared_by"] = "@" + request.user.username
	        del post["_id"]
	        self.insert_post(post)
	        return True
	    else:
	        return False


class Blog(CommunityShareBase):
	def __init__(self):
		super('blog')


class Forum(CommunityShareBase):
	def __init__(self):
		super('forum')