from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'vmicroc.views.home', name='home'),
    url(r'^about/$', 'vmicroc.views.about', name='about'),
    url(r'^contact/$', 'vmicroc.views.contact', name='contact'),

    # The page for inspecting results.
    url(r'^inspector/$', 'locations.views.inspector', name='inspector'),
    url(r'^inspector/iframe/$', 'locations.views.inspector', {'base_template': 'simple.html'}, name='inspector-iframe'),

    url(r'^location/(?P<location_id>\w+)/summary/$', 'locations.views.summary_data', name='summary_data'),
    url(r'^location/(?P<location_id>\w+)/detail/$', 'locations.views.detail_data', name='detail_data'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
