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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
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
from horizon.utils import memoized

from .forms import CreateNetwork
from .forms import CreateGateway
from .forms import AddSite
from .forms import GetBranchGwVM
from .forms import GetBranchVM
from .forms import AddGW
from .forms import PreAddLink
from .forms import AutoBurst

from .tables import NetworksTable
from .workflows import CreateVPN
#from .workflows import CreateGW
#from links.workflows import CreateLink
import requests
from openstack_dashboard.dashboards.project.ipsec \
    import forms as project_forms
from openstack_dashboard.dashboards.project.ipsec\
    import tables as project_tables
from openstack_dashboard.dashboards.project.ipsec\
    import workflows as project_workflows

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
#class IndexView(tabs.TabbedTableView):
    table_class = NetworksTable
    template_name = 'project/ipsec/index.html'
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
            vpns = api.elasticnet.getVPNList(self)
            for vpn in vpns:
                LOG.debug("IPSEC in views: {0}".format(vpn.getInfo()))
        except:
            vpns = []
            msg = _('Unable to retrieve elastic network list.')
            exceptions.handle(self.request, msg)
        return vpns

class UpdateView(forms.ModalFormView):
    context_object_name = 'vpn'
    form_class = project_forms.UpdateVPN
    form_id = "update_vpn_form"
    modal_header = _("Edit IPSEC")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:ipsec:update"
    success_url = reverse_lazy("horizon:project:ipsec:index")
    template_name = 'project/ipsec/update.html'
    page_title = _("Update IPSEC")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['id'],)
        context["id"] = self.kwargs['id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        vpn_id = self.kwargs['id']
        try:
	    vpns = api.elasticnet.getVPNList(self)
            for vpn in vpns:
                return vpn
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve ipsec details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        network = self._get_object()
        vpns = api.elasticnet.getVPNList(self)
        return vpns

class CreateNetworkView(workflows.WorkflowView):
    workflow_class = CreateVPN
    template_name = 'project/ipsec/create.html'

    def get_initial(self):
        pass

class CreateVPNView(workflows.WorkflowView):
    workflow_class = CreateVPN
    template_name = 'project/ipsec/createvpn.html'
   
    def get_initial(self):
        initial = super(CreateVPNView, self).get_initial()
	return initial
        '''try:
            gateways = api.elasticnet.getVPNList(self)
            for gateway in gateways:
        except:
            gateways = []
            msg = _('Unable to retrieve elastic network list.')
            exceptions.handle(self.request, msg)
        return gateways'''


class AddGWView(forms.ModalFormView):
    form_class = AddGW
    template_name = 'project/ipsec/addgw.html'

class AddSiteView(forms.ModalFormView):
    form_class = AddSite
    template_name = 'project/ipsec/addsite.html'
    success_url = 'horizon:project:ipsec:index'
   
    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        print "+++++222RBA +++++++  %s"%self.kwargs['vpn_id']
        vpn_id=self.kwargs['vpn_id']
        return {'vpn_id': self.kwargs['vpn_id']}

    def get_data(self):
        print "++++333 RBA ++++ %s"%self.kwargs['vpn_id']
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, **kwargs):
        context = super(AddSiteView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

class DownloadBranchGwVM(TemplateView):
    success_url = 'horizon:project:ipsec:downloadbranchgwvm'
    template_name = 'project/ipsec/downloadbranchgwvm.html'
    def get_data(self):
        vpn_id=self.kwargs['vpn_id']
        return vpn_id

    def get_context_data(self, vpn_id=None):
        return {'vpn_id': vpn_id}

class DownloadBranchVM(TemplateView):
    success_url = 'horizon:project:ipsec:downloadbranchvm'
    template_name = 'project/ipsec/downloadbranchvm.html'

    
class GetBranchVM(forms.ModalFormView):
    form_class = GetBranchVM
    template_name = 'project/ipsec/getbranchvm.html'
    success_url = 'horizon:project:ipsec:downloadbranchvm'

    def get_success_url(self):
        return reverse(self.success_url)


class GetBranchGwVM(forms.ModalFormView):
    form_class = GetBranchGwVM
    template_name = 'project/ipsec/getbranchgwvm.html'
    success_url = 'horizon:project:ipsec:downloadbranchgwvm'

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
    template_name = 'project/ipsec/addgw.html'
    success_url = 'horizon:project:ipsec:index'

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
    template_name = 'project/ipsec/autoburst.html'
    success_url = 'horizon:project:ipsec:index'

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
    template_name = 'project/ipsec/preaddlink.html'
    success_url = 'horizon:project:ipsec:index'

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
    template_name = 'project/ipsec/addlink.html'
    success_url = 'horizon:project:ipsec:index'

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

