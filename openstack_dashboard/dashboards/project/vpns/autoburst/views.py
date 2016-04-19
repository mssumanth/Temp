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

#from horizon import api
from horizon import forms
from horizon import tables
from horizon import exceptions

from .forms import DelLink
from .tables import LinksTable
from .forms import DeleteLink

import pickle
LOG = logging.getLogger(__name__)

class LinksView(tables.DataTableView):
    table_class = LinksTable
    template_name = 'project/vpns/links/index.html'

    def get_data(self):
        network_id = self.kwargs['vpn_id']
        try:
            links = api.elasticnet.elasticnet_list_links(self.request, network_id)
	    print "++++++++++++ links=%s"%links
        except:
            links = []
            msg = _('Unable to retrieve network details.')
            exceptions.handle(self.request, msg)
        return links

class DelLinkView(forms.ModalFormView):
    form_class = DelLink
    template_name = 'project/vpns/links/dellink.html'
    success_url = 'horizon:project:vpns:links:links'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['vpn_id'],))

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        link_id=self.kwargs['link_id']
        return {'vpn_id': self.kwargs['vpn_id'],'link_id': self.kwargs['link_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
	link_id=self.kwargs['link_id']
        return {'vpn_id': self.kwargs['vpn_id'],'link_id': self.kwargs['link_id']}


    def get_context_data(self, **kwargs):
        context = super(DelLinkView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        context["link_id"] = self.kwargs['link_id']
        return context

class DeleteLinkView(forms.ModalFormView):
    form_class = DeleteLink
    template_name = 'project/vpns/links/deletelink.html'
    success_url = 'horizon:project:vpns:links:links'
    def get_context_data(self, **kwargs):
        context = super(DeleteLinkView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

