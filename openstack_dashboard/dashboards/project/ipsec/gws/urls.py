from django.conf.urls import patterns
from django.conf.urls import url

from .views import GWsView

GWS = r'^(?P<gw_id>[^/]+)/%s$'

# Quantum Network Ports
urlpatterns = patterns('openstack_dashboard.dashboards.project.vpns.gws.views',
    url(
        r'^(?P<elasticnet_id>[^/]+)/gws/$',
        GWsView.as_view(),
        name='gws'),
)
