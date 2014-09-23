from django.conf.urls import include, patterns, url
from django.views.generic import RedirectView


urlpatterns = patterns(
    'moocng.profile.views',
    url(r'^user/(?P<user_slug>[-\w]+)/$', 'profile_overview',
        name='profile_overview'),
)
