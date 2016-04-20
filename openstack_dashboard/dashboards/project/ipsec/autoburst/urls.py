from django.conf.urls import patterns
from django.conf.urls import url

from .views import LinksView, DelLinkView


# Quantum Network Ports
urlpatterns = patterns('horizon.dashboards.nova.elasticnets.links.views',
    url(
        r'^(?P<vpn_id>[^/]+)/links/$',
        LinksView.as_view(),
        name='links'),
    url(
        r'^(?P<vpn_id>[^/]+)/(?P<link_id>[^/]+)/dellink/$',
        DelLinkView.as_view(),
        name='dellink'),
)


