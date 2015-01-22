import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import render_flatpage
from django.contrib.sites.models import get_current_site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import get_language
from django.utils.translation import ugettext as _


from moocng.profile.models import (	UserProfile, get_blog_user, get_posts, 
									insert_post, count_posts, update_following_blog_user, 
									insert_blog_user, save_retweet, get_num_followers, search_posts)

from moocng.courses.security import (get_courses_available_for_user,
									get_courses_user_is_enrolled,
									get_course_progress_for_user)
from moocng.courses.utils import (is_teacher as is_teacher_test)
from moocng.badges.utils import (get_user_badges_group_by_course)

from moocng.slug import unique_slugify
from moocng.utils import use_cache
from moocng.profile.forms import (PostForm)
from moocng.mongodb import get_micro_blog_db
from moocng.mongodb import get_db
from moocng.portal.templatetags.gravatar import (gravatar_for_email)
import pymongo
import json
from bson import json_util
from dateutil import tz
from datetime import date, datetime
from moocng.profile.utils import (get_user)
from cgi import escape
from django.utils.html import urlize

def profile_timeline(request):
	return render_to_response('profile/timeline.html', {
		'profile': {},
		'request': request
		}, context_instance=RequestContext(request))

def profile_groups(request):
	return render_to_response('profile/groups.html', {
		'profile': {},
		'request': request
		}, context_instance=RequestContext(request))

# @login_required
def profile_courses(request, id):

	if(not id):
		if(not request.user.id):
			return HttpResponseRedirect("/auth/login")
		user = request.user
		id = request.user.id
	else:
		user = User.objects.get(username=id)
		id = user.id

	case = _getCase(request,id)

	courses = get_courses_user_is_enrolled(user)
	courses_completed = 0
	for course in courses:
		if request.user.is_authenticated():
			course.is_enrolled = course.students.filter(id=user.id).exists()
			course.is_teacher = is_teacher_test(user, course)
			course.progress = get_course_progress_for_user(course, user)
			if course.progress == 100:
				courses_completed +=1
		else:
			course.is_enrolled = False
			course.is_teacher = False

	return render_to_response('profile/courses.html', {
		"id":id,
		"case":case,
		'request': request,
		'courses': courses,
		'courses_completed': courses_completed,
		"user_view_profile": user,
		"badges_count": get_db().get_collection('badge').find({"id_user": id}).count()
		}, context_instance=RequestContext(request))

# @login_required
def profile_badges(request, id):

	if(not id):
		if(not request.user.id):
			return HttpResponseRedirect("/auth/login")
		user = request.user
		id = request.user.id
	else:
		user = User.objects.get(username=id)
		id = user.id

	courses = get_user_badges_group_by_course(user)

	return render_to_response('profile/badges.html', {
		"id":id,
		'request': request,
		"user_view_profile": user,
		"badges_count": get_db().get_collection('badge').find({"id_user": id}).count(),
		"courses": courses,
		}, context_instance=RequestContext(request))

@login_required
def profile_calendar(request):
	return render_to_response('profile/calendar.html', {
		'profile': {},
		'request': request,
		}, context_instance=RequestContext(request))

# @login_required
def profile_user(request, id):

	if(not id):
		if(not request.user.id):
			return HttpResponseRedirect("/auth/login")
		id = request.user.id
		user =  request.user
	else:
		user = User.objects.get(username=id)
		id = user.id

	courses = get_courses_user_is_enrolled(user)

	return render_to_response('profile/user.html', {
		"id":id,
		"badges_count": get_db().get_collection('badge').find({"id_user": id}).count(),
		'request': request,
		'courses': courses,
		'is_user': True,
		"user_view_profile": user,
		}, context_instance=RequestContext(request))

# @login_required
def profile_posts(request, id):
	if(not id):
		if(not request.user.id):
			return HttpResponseRedirect("/auth/login")
		id = request.user.id
		user = request.user
	else:
		user = User.objects.get(username=id)
		id = user.id

	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			insert_post({
							"id_user": request.user.id, 
							"first_name": request.user.first_name,
							"last_name":request.user.last_name,
							"username": "@" + request.user.username,
							"gravatar": "http:" + gravatar_for_email(request.user.email),
							"date": datetime.utcnow().isoformat(),
							"text": urlize(escape(form.cleaned_data['postText'])),
							"children": [],
							"favourite": [],
							"shared": 0

						})

			return HttpResponseRedirect("/user/posts")
	
	else:
		case = _getCase(request,id)

		blog_user = get_blog_user(request.user.id)
		if(blog_user and id in blog_user["following"]):
			following = "true"
		else:
			following = "false"

		followingCount = 0
		if(request.user.id != id):
			blog_user = get_blog_user(id)
			if(blog_user):
				followingCount = len(blog_user["following"])
		elif(blog_user):
			followingCount = len(blog_user["following"])


		listPost = get_posts(case, id, blog_user, 0)
		
		return render_to_response('profile/posts.html', {
			"id":id,
			"badges_count": get_db().get_collection('badge').find({"id_user": id}).count(),
			# "email":"@" + request.user.email.split("@")[0],
			'request': request,
			'form': PostForm(),
			'totalPost': count_posts(id),
			'posts': listPost,
			'case': case,
			"user_view_profile": user,
			"following": following,
			"followingCount": followingCount,
			"followerCount": get_num_followers(id)
			}, context_instance=RequestContext(request))

def profile_posts_search(request, query, hashtag=False):
	if(not request.user.id):
		return HttpResponseRedirect("/auth/login")
	id = request.user.id
	user = request.user

	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			insert_post({
							"id_user": request.user.id, 
							"first_name": request.user.first_name,
							"last_name":request.user.last_name,
							"username": "@" + request.user.username,
							"gravatar": "http:" + gravatar_for_email(request.user.email),
							"date": datetime.utcnow().isoformat(),
							"text": urlize(escape(form.cleaned_data['postText'])),
							"children": [],
							"favourite": [],
							"shared": 0

						})

			return HttpResponseRedirect("/user/posts")
	
	else:
		case = _getCase(request,id)

		blog_user = get_blog_user(request.user.id)
		if(blog_user and id in blog_user["following"]):
			following = "true"
		else:
			following = "false"

		followingCount = 0
		if(request.user.id != id):
			blog_user = get_blog_user(id)
			if(blog_user):
				followingCount = len(blog_user["following"])
		elif(blog_user):
			followingCount = len(blog_user["following"])

		if hashtag:
			search_query = '#%s' % (query)
		else:
			search_query = query
		listPost = search_posts(search_query, 0)
		
		return render_to_response('profile/posts_search.html', {
			"id":id,
			"badges": get_db().get_collection('badge').find({"id_user": id}).count(),
			# "email":"@" + request.user.email.split("@")[0],
			'request': request,
			'form': PostForm(),
			'totalPost': count_posts(id),
			'posts': listPost,
			'case': case,
			"user_view_profile": user,
			"following": following,
			"followingCount": followingCount,
			"followerCount": get_num_followers(id),
			"query": query,
			"is_hashtag": hashtag,
			}, context_instance=RequestContext(request))


# @login_required
def load_more_posts(request, page, query, search=False, hashtag=False):
	page = int(page)
	listPost = None
	if search and query:
		if hashtag:
			query = "#%s" % (query)
		listPost = search_posts(query, page)
	else:
		if(not query):
			id = request.user.id
		else:
			id = int(query)
		listPost = get_posts(0, id, get_blog_user(request.user.id), page)

	return render_to_response('profile/post.html', {
			'request': request,
			'posts': listPost
			}, context_instance=RequestContext(request))

@login_required
def user_follow(request, id, follow):
	id = int(id)
	user = get_blog_user(request.user.id) 

	if(follow == "0"):
		if(user):
			if(not id in user["following"]):
				user["following"].append(id)
				update_following_blog_user(request.user.id, user["following"])
		else:
			insert_blog_user({
									"id_user": request.user.id, 
									"following": [id]
								  })
	
	elif(follow == "1" and user):
		user["following"].remove(id)
		update_following_blog_user(request.user.id, user["following"] )

	return HttpResponse("true")

@login_required
def retweet(request, id):
	return HttpResponse(save_retweet(request,id))

def _getCase(request, id):
	if(not request.user or not request.user.id):
		return 2

	if(not id):
		return 0

	if(request.user.id != id):
		return 1
	else:
		return 0


