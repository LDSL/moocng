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

from moocng.slug import unique_slugify
from moocng.utils import use_cache

def profile_overview(request, user_slug):
	user = {
		'cn': 'Raul',
		'sn': 'Yeguas',
		'username': 'neokore',
		'get_full_name': 'Raul Yeguas',
		'email': 'neokore@gmail.com',
	}

	return render_to_response('profile/overview.html', {
		'user': user
		}, context_instance=RequestContext(request))


