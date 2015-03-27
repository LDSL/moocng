from django.conf.urls import include, patterns, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse


urlpatterns = patterns(
    'moocng.profile.views',
    url(r'^user/timeline$', 'profile_timeline',
        name='profile_timeline'),
    url(r'^user/groups$', 'profile_groups',
        name='profile_groups'),
   

   url(r'^user/courses/(?P<id>[-\w.]*)$', 'profile_courses',
        name='profile_courses'),
   
    url(r'^user/courses/$', 'profile_courses',
        name='profile_courses'),

    url(r'^user/badges/(?P<id>[-\w.]*)$', 'profile_badges',
        name='profile_badges'),
    
    url(r'^user/calendar/$', 'profile_calendar',
        name='profile_calendar'),
   
    url(r'^user/profile/(?P<id>[-\w.]*)$', 'profile_user',
        name='profile_user'),

    url(r'^user/profile/$', 'profile_user',
        name='profile_user'),
   
    url(r'^user/posts/(?P<id>[-\w.]*)$', 'profile_posts',
        name='profile_posts'),

    url(r'^user/posts/$', 'profile_posts',
        name='profile_posts'),

    url(r'^user/posts/search/(?P<query>[-\w.]+)$', 'profile_posts_search',
        name='profile_posts_search'),

    url(r'^user/posts/hashtag/(?P<query>[-\w.]+)$', 'profile_posts_search',
        {'hashtag': True}, name='profile_posts_hashtag'),

    url(r'^user/loadMorePosts/(?P<page>[-\w]+)/(?P<query>[-\w.]+)$', 'load_more_posts',
        name='load_more_posts'),
    
    url(r'^user/loadMorePosts/search/(?P<page>[-\w]+)/(?P<query>[-\w.]+)$', 'load_more_posts',
        {'search': True}, name='load_more_posts_search'),

    url(r'^user/loadMorePosts/hashtag/(?P<page>[-\w]+)/(?P<query>[-\w.]+)$', 'load_more_posts',
        {'search': True, 'hashtag': True}, name='load_more_posts_hashtag'),

    url(r'^user/userFollow/(?P<id>[-\w.]+)/(?P<follow>[-\w.]+)$', 'user_follow',
        name='user_follow'),

    url(r'^user/retweet/(?P<id>[-\w.]+)$', 'retweet',
        name='retweet'),

    url(r'^user/reply/(?P<id>[-\w.]+)$', 'reply',
        name='reply'),
)
