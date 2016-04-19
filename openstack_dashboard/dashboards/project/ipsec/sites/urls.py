from django.conf.urls import patterns
from django.conf.urls import url

from .views import SitesView

urlpatterns = patterns('openstack_dashboard.dashboards.project.vpns.sites.views',
    url(
        r'^(?P<vpn_id>[^/]+)/sites/$',
        SitesView.as_view(),
        name='sites'),
)
