from django.conf.urls import include, patterns, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse


urlpatterns = patterns(
    'moocng.profile.views',
    url(r'^user/(?P<user_slug>[-\w]+)/timeline$', 'profile_timeline',
        name='profile_timeline'),
    url(r'^user/(?P<user_slug>[-\w]+)/groups$', 'profile_groups',
        name='profile_groups'),
    url(r'^user/(?P<user_slug>[-\w]+)/courses$', 'profile_courses',
        name='profile_courses'),
    url(r'^user/(?P<user_slug>[-\w]+)/calendar$', 'profile_calendar',
        name='profile_calendar'),
    url(r'^user/(?P<user_slug>[-\w]+)/profile$', 'profile_user',
        name='profile_user'),
)
