from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin
admin.autodiscover()

from rainmap import settings
from rainmap.core.views import profile

urlpatterns = patterns('',
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/', include(admin.site.urls)),
    url(r'^profile/',
        profile,
        {'template': 'core/profile.html'},
        name='user_profile'),
    (r'^scans/', include('rainmap.core.urls')),
    url(r'^$', 'rainmap.core.views.index', name='index'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^storage/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.OUTPUT_ROOT}),
        url(r'^(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
)
