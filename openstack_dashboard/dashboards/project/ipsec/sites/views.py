# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright Cisco Systems Inc.
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

"""
Views for managing Nova keypairs.
"""
import logging

from django import http
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.views.generic import View, TemplateView
from django.utils.translation import ugettext as _

from openstack_dashboard import api

from horizon import forms
from horizon import tables
from horizon import exceptions

from .tables import SitesTable

import pickle
LOG = logging.getLogger(__name__)

class SitesView(tables.DataTableView):
    table_class = SitesTable
    template_name = 'project/vpns/sites/index.html'
    
    def get_data(self):
        network_id = self.kwargs['vpn_id']
        try:
            sites = api.elasticnet.elasticnet_list_sites(self.request, network_id)
	    print "++++++++++++ sites=%s"%sites
        except:
            sites = []
            msg = _('Unable to retrieve network details.')
            exceptions.handle(self.request, msg)
        return sites

    def get_context_data(self, **kwargs):
        context = super(SitesView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

    def get_success_url(self):
        return reverse("horizon:project:vpns:sites:sites",
                       args=(self.kwargs['vpn_id'],))


