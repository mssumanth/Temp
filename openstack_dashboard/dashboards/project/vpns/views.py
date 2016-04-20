# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from openstack_dashboard.api import elasticnet
from openstack_dashboard import api

from horizon import forms
from horizon import tables
from horizon import exceptions
from horizon import workflows
from horizon import tabs

from .forms import CreateNetwork
from .forms import CreateGateway
from .forms import AddSite
from .forms import GetBranchGwVM
from .forms import GetBranchVM
from .forms import AddGW
from .forms import PreAddLink
from .forms import AutoBurst

from .tables import NetworksTable
from openstack_dashboard.dashboards.project.instances \
            import tables as project_tables

from .workflows import CreateVPN
from .workflows import CreateGW
#from links.workflows import CreateLink
import requests

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
#class IndexView(tabs.TabbedTableView):
    table_class = NetworksTable
    template_name = 'project/vpns/index.html'
    #template_name = 'project/instances/index.html'
    
    def get_data(self):
        try:
            '''networks = api.elasticnet.elasticnet_network_list(self.request)
            headers = {'content-type': 'application/json'}
            url = 'http://127.0.0.1:7007/create_gateway'
            responses = requests.get(url, verify=False, headers = headers)
            
            rsp = []
            for response in responses.json()['create_gateway']:
                rsp.append(
            '''
            #networks = api.network_base.FloatingIpManager.list_pools(self.request)
            gateways = api.elasticnet.getGatewayList(self)
        except:
            gateways = []
            msg = _('Unable to retrieve elastic network list.')
            exceptions.handle(self.request, msg)
        return gateways

class CreateNetworkView(workflows.WorkflowView):
    workflow_class = CreateVPN
    template_name = 'project/vpns/create.html'

    def get_initial(self):
        pass

class CreateGatewayView(workflows.WorkflowView):
    workflow_class = CreateGW
    template_name = 'project/vpns/creategw.html'
    
    def get_initial(self):
        initial = super(CreateGatewayView, self).get_initial()
        return initial

class AddGWView(forms.ModalFormView):
    form_class = AddGW
    template_name = 'project/vpns/addgw.html'

class AddSiteView(forms.ModalFormView):
    form_class = AddSite
    template_name = 'project/vpns/addsite.html'
    success_url = 'horizon:project:vpns:index'
   
    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(AddSiteView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

class DownloadBranchGwVM(TemplateView):
    success_url = 'horizon:project:vpns:downloadbranchgwvm'
    template_name = 'project/vpns/downloadbranchgwvm.html'
    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, vpn_id=None):
        return {'vpn_id': vpn_id}

class DownloadBranchVM(TemplateView):
    success_url = 'horizon:project:vpns:downloadbranchvm'
    template_name = 'project/vpns/downloadbranchvm.html'

    
class GetBranchVM(forms.ModalFormView):
    form_class = GetBranchVM
    template_name = 'project/vpns/getbranchvm.html'
    success_url = 'horizon:project:vpns:downloadbranchvm'

    def get_success_url(self):
        return reverse(self.success_url)


class GetBranchGwVM(forms.ModalFormView):
    form_class = GetBranchGwVM
    template_name = 'project/vpns/getbranchgwvm.html'
    success_url = 'horizon:project:vpns:downloadbranchgwvm'

    def get_success_url(self):
        return reverse(self.success_url,  kwargs={"vpn_id": self.kwargs['vpn_id']})

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(GetBranchGwVM, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context


class AddGWView(forms.ModalFormView):
    form_class = AddGW
    template_name = 'project/vpns/addgw.html'
    success_url = 'horizon:project:vpns:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(AddGWView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context


class AutoBurstView(forms.ModalFormView):
    form_class = AutoBurst
    template_name = 'project/vpns/autoburst.html'
    success_url = 'horizon:project:vpns:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(AutoBurstView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context



class PreAddLinkView(forms.ModalFormView):
    form_class = PreAddLink
    template_name = 'project/vpns/preaddlink.html'
    success_url = 'horizon:project:vpns:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(PreAddLinkView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context



class AddLinkView(forms.ModalFormView):
    form_class = PreAddLink
    template_name = 'project/vpns/addlink.html'
    success_url = 'horizon:project:vpns:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(PreAddLinkView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

