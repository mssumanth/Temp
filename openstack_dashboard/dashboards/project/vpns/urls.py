# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Cisco Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
#from django.conf.urls.defaults import *

#from .ports import urls as port_urls
from .sites import urls as site_urls
from .gws import urls as gw_urls
from .links import urls as link_urls
from .views import IndexView, CreateNetworkView, CreateGatewayView
from .views import AddSiteView, AddGWView, PreAddLinkView, DownloadBranchGwVM, DownloadBranchVM, GetBranchGwVM, GetBranchVM, AddLinkView, AutoBurstView
from .links.views import DeleteLinkView

VPN = r'^(?P<vpn_id>[^/]+)/%s$'


urlpatterns = patterns('openstack_dashboard.dashboards.project.vpns.views',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^create/$', CreateNetworkView.as_view(), name='create'),
    url(r'^creategw/$', CreateGatewayView.as_view(), name='creategw'),
    url(r'^(?P<vpn_id>[^/]+)/addsite/$', AddSiteView.as_view(), name='addsite'),
    url(r'^(?P<vpn_id>[^/]+)/getbranchgwvm/$', GetBranchGwVM.as_view(), name='getbranchgwvm'),
    url(r'^getbranchvm/$', GetBranchVM.as_view(), name='getbranchvm'),
    url(r'^(?P<vpn_id>[^/]+)/downloadbranchgwvm/$', DownloadBranchGwVM.as_view(), name='downloadbranchgwvm'),
    url(r'^downloadbranchvm/$', DownloadBranchVM.as_view(), name='downloadbranchvm'),
    url(r'^(?P<vpn_id>[^/]+)/addgw/$', AddGWView.as_view(), name='addgw'),
    url(r'^(?P<vpn_id>[^/]+)/preaddlink/$', PreAddLinkView.as_view(), name='preaddlink'),
    url(r'^(?P<vpn_id>[^/]+)/autoburst/$', AutoBurstView.as_view(), name='autoburst'),
    url(r'^(?P<vpn_id>[^/]+)/deletelink/$', DeleteLinkView.as_view(),name='deletelink'),
    url(r'^sites/', include(site_urls, namespace='sites')),
    url(r'^gws/', include(gw_urls, namespace='gws')),
    url(r'^links/', include(link_urls, namespace='links')),
)
