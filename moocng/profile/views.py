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
from datetime import date

from moocng.profile.models import UserProfile
from moocng.courses.security import (get_courses_available_for_user)

from moocng.slug import unique_slugify
from moocng.utils import use_cache

def profile_timeline(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'raul.yeguas',
		'get_full_name': 'Raul Yeguas',
		'email': 'raul.yeguas@geographica.gs',
		'badges': ['badge1','badge2'],
		'karma': 15,
		'social': {
			'posts': 3,
			'followers': '15K',
			'followings': 1,
			'starred': 359,
			'lists': ['Mesozoico', 'RMS can\'t skate', 'Linus vs nVidia']
		},
		'slug': user_slug
	}

	return render_to_response('profile/timeline.html', {
		'user': user,
		'request': request,
		'user_slug': user_slug
		}, context_instance=RequestContext(request))

def profile_groups(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'raul.yeguas',
		'get_full_name': 'Raul Yeguas',
		'email': 'raul.yeguas@geographica.gs',
		'badges': ['badge1','badge2'],
		'karma': 15,
		'social': {
			'posts': 3,
			'followers': '15K',
			'followings': 1,
			'starred': 359,
			'lists': ['Mesozoico', 'RMS can\'t skate', 'Linus vs nVidia']
		},
		'slug': user_slug
	}

	return render_to_response('profile/groups.html', {
		'user': user,
		'request': request
		}, context_instance=RequestContext(request))

@login_required
def profile_courses(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'raul.yeguas',
		'get_full_name': 'Raul Yeguas',
		'email': 'raul.yeguas@geographica.gs',
		'badges': ['badge1','badge2'],
		'karma': 15,
		'social': {
			'posts': 3,
			'followers': '15K',
			'followings': 1,
			'starred': 359,
			'lists': ['Mesozoico', 'RMS can\'t skate', 'Linus vs nVidia']
		},
		'slug': user_slug,
	}

	courses = get_courses_available_for_user(request.user)

	return render_to_response('profile/courses.html', {
		'user': user,
		'request': request,
		'courses': courses
		}, context_instance=RequestContext(request))

@login_required
def profile_calendar(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'raul.yeguas',
		'get_full_name': 'Raul Yeguas',
		'email': 'raul.yeguas@geographica.gs',
		'badges': ['badge1','badge2'],
		'karma': 15,
		'social': {
			'posts': 3,
			'followers': '15K',
			'followings': 1,
			'starred': 359,
			'lists': ['Mesozoico', 'RMS can\'t skate', 'Linus vs nVidia']
		},
		'slug': user_slug,
	}

	courses = get_courses_available_for_user(request.user)

	return render_to_response('profile/calendar.html', {
		'user': user,
		'request': request,
		'courses': courses
		}, context_instance=RequestContext(request))

@login_required
def profile_user(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'raul.yeguas',
		'get_full_name': 'Raul Yeguas',
		'email': 'raul.yeguas@geographica.gs',
		'badges': ['badge1','badge2'],
		'karma': 15,
		'social': {
			'posts': 3,
			'followers': '15K',
			'followings': 1,
			'starred': 359,
			'lists': ['Mesozoico', 'RMS can\'t skate', 'Linus vs nVidia']
		},
		'slug': user_slug,
		'location': 'Spain',
		'languages': ['Spanish', 'English'],
		'sex': 'Male',
		'birth': date(1986, 3, 1),
		'personalweb': 'http://geographica.gs',
		'bio': '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed pellentesque accumsan nunc, sed tempor justo efficitur vel. Proin a nisi urna. Aliquam ac augue leo. Duis in mollis est, in posuere enim. Ut efficitur dignissim est eget viverra. Fusce ultrices est nec turpis tincidunt, eget tincidunt sapien vulputate.</p><p>Maecenas hendrerit aliquam semper. Aliquam venenatis commodo porttitor. Pellentesque finibus, nisl vel ornare consectetur, arcu sem mattis est, vitae finibus augue velit a est. Suspendisse sollicitudin, eros ut finibus luctus, orci est commodo nibh, et lobortis quam quam at nisi. Phasellus suscipit et dui ac porttitor. Suspendisse ac semper nibh, nec cursus enim. Suspendisse non purus vitae odio imperdiet sagittis.</p><p>Mauris id lorem ligula. Mauris finibus rutrum risus, id malesuada nunc scelerisque et. Maecenas hendrerit egestas dignissim.</p>',
		'socialmedia': [
			{
				'name': 'facebook',
				'url': 'http://facebook.com/'
			},
			{
				'name': 'twitter',
				'url': 'http://twitter.com/'
			},
			{
				'name': 'google',
				'url': 'http://plus.google.com/'
			},
			{
				'name': 'linkedin',
				'url': 'http://linkedin.com/'
			},
		],
		'interests': ['Science', 'Geology', 'Technology', 'Design']
	}

	courses = get_courses_available_for_user(request.user)

	return render_to_response('profile/user.html', {
		'user': user,
		'request': request,
		'courses': courses,
		'is_user': True
		}, context_instance=RequestContext(request))

