# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Cisco Systems Inc.
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


from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

import logging
from django.core import urlresolvers
#from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.utils import http
#from django.utils.translation import ugettextG as _
from django.template import defaultfilters as filters

from openstack_dashboard.api import elasticnet
from openstack_dashboard import api
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

#from horizon import api
from horizon import tables
from horizon.utils.filters import replace_underscores
from links.tables import DeleteLink
from openstack_dashboard import policy
import requests
import json

LOG = logging.getLogger(__name__)

class GetBranchGwVM(tables.LinkAction):
    name = "getbranchgwvm"
    verbose_name = _("Get Branch GW VM")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:getbranchgwvm"
    def get_link_url(self, datum=None):
        print "+++RBA RBA+++++++++++++++++++++++++ datum.id=%s"%datum.id
        urlfromview=reverse(
            'horizon:project:vpns:getbranchgwvm',
            args=[datum.id])
        print "+++ RBA RBA +++++ url=%s"%urlfromview
        return urlfromview

class GetBranchVM(tables.LinkAction):
    name = "getbranchvm"
    verbose_name = _("Get Branch VM")
    classes = ("ajax-modal", "btn-create")
    url = 'horizon:project:vpns:getbranchvm'
    def get_link_url(self, datum=None):
        urlfromview=reverse(
	    'horizon:project:vpns:getbranchvm')
	    #args=[datum.id])
            #'horizon:openstack_dashboard:dashboards:project:vpns:getbranchvm')
        return shortcuts.redirect(urlfromview)

class AddSite(tables.LinkAction):
    name = "addsite"
    verbose_name = _("Add Site")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:addsite"
    def get_link_url(self, datum=None):
        print "+++RBA RBA+++++++++++++++++++++++++ datum.id=%s"%datum.id
        urlfromview=reverse(
            'horizon:project:vpns:addsite',
            args=[datum.id])
        print "+++ RBA RBA +++++ url=%s"%urlfromview
        return urlfromview

class AddGW(tables.LinkAction):
    name = "addgw"
    verbose_name = _("Add GW")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:addgw"
    def get_link_url(self, datum=None):
        return urlresolvers.reverse(
            'horizon:project:vpns:addgw',
            args=[datum.id])

class UpdateRow(tables.Row):
   ajax = True

   def get_data(self, request, obj_id):
	enet=api.elasticnet.elasticnet_network_get(request, obj_id)
	print "+++++ obj_id=%s, enet=%s"%(obj_id,enet)
        return enet


class DeleteNetworks(tables.DeleteAction):
    data_type_singular = _("Virtual Private Network")
    data_type_plural = _("Virtual Private Networks")

    def delete(self, request, obj_id):
        api.elasticnet.elasticnet_network_delete(request, obj_id)

    def handle(self, table, request, object_ids):
        # Overriden to show clearer error messages instead of generic message
        deleted = []
        for obj_id in object_ids:
            obj = table.get_object_by_id(obj_id)
            try:
                self.delete(request, obj_id)
                deleted.append(obj)
            except:
                LOG.exception('Unable to delete vpn "%s".' % obj.name)
                messages.error(request,
                               _('Unable to delete vpn with ports: %s') %
                               obj.name)
        if deleted:
            messages.success(request,
                             _('Successfully deleted networks: %s')
                               % ", ".join([obj.name for obj in deleted]))
        return shortcuts.redirect('horizon:project:vpns:index')


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Virtual Private Network")
    url = "horizon:project:vpns:create"
    classes = ("ajax-modal", "btn-create")

class CreateGateway(tables.LinkAction):
    name = "createGw"
    verbose_name = _("Create Gateway")
    url = "horizon:project:vpns:creategw"
    classes = ("ajax-modal", "btn-create")

'''class DeleteGateway(tables.LinkAction):
    name = "deleteGw"
    verbose_name = _("Delete Gateway")
    url = "horizon:project:vpns:deletegw"
    classes = ("ajax-modal", "btn-create")'''

class PreAddLink(tables.LinkAction):
    name = "preaddlink"
    verbose_name = _("Connect Link")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:preaddlink"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:vpns:preaddlink',
            args=[datum.id])

class AutoBurst(tables.LinkAction):
    name = "autoburst"
    verbose_name = _("Use for Auto Burst")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:autoburst"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:vpns:autoburst',
            args=[datum.id])

class AddLink(tables.LinkAction):
    name = "addlink"
    verbose_name = _("Add Link")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:vpns:preaddlink"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:vpns:preaddlink',
            args=[datum.id])

class RequestBandwidth(tables.LinkAction):
    name = "requestbandwidth"
    verbose_name = _("Request Bandwidth")
    url = "horizon:project:vpns:reqbw"
    classes = ("ajax-modal", "btn-create")

class DeleteSite(tables.LinkAction):
    name = "deletesite"
    verbose_name = _("Delete Site")
    url = "horizon:project:vpns:delsite"
    classes = ("ajax-modal", "btn-create")

class CheckGatewayEditable(object):
    """Mixin class to determine the specified network is editable."""
    def allowed(self, request, datum=None):
        # Only administrator is allowed to create and manage shared networks.
        if datum and datum.shared:
            return False
        return True

class DeleteGateway(tables.DeleteAction):
    name = "deleteGateway"
    data_type_singular = _("Gateway")
    data_type_plural = _("Gateways")

    def delete(self, request, gateway_id):
        try:
            gw_url = 'http://127.0.0.1:7007/delete_gateway'
            gw_id = gateway_id
            # Send the delete request.
            payload = {'gw_id': gw_id}
            headers = {'content-type': 'application/json'}
	    rsp = requests.post(gw_url, data=json.dumps(payload), headers = headers)
        except Exception:
            msg = _('Failed to delete gateway%s')
            redirect = reverse("horizon:project:vpns:index")
            exceptions.handle(request, msg % gw_id, redirect=redirect)
        

def get_ips(instance):
    template_name = 'project/instances/_instance_ips.html'
    ip_groups = {}

    for ip_group, addresses in instance.addresses.iteritems():
        ip_groups[ip_group] = {}
        ip_groups[ip_group]["floating"] = []
        ip_groups[ip_group]["non_floating"] = []

        for address in addresses:
            if ('OS-EXT-IPS:type' in address and
               address['OS-EXT-IPS:type'] == "floating"):
                ip_groups[ip_group]["floating"].append(address)
            else:
                ip_groups[ip_group]["non_floating"].append(address)

    context = {
        "ip_groups": ip_groups,
    }
    return template.loader.render_to_string(template_name, context)

def get_keyname(instance):
    if hasattr(instance, "keypair"):
        keyname = instance.keypair
        return keyname
    return _("Not available")

'''def get_size(instance):
    if hasattr(instance, "full_flavor"):
        template_name = 'project/instances/_instance_flavor.html'
        size_ram = sizeformat.mb_float_format(instance.full_flavor.ram)
        if instance.full_flavor.disk > 0:
            size_disk = sizeformat.diskgbformat(instance.full_flavor.disk)
        else:
            size_disk = _("%s GB") % "0"
        context = {
            "name": instance.full_flavor.name,
            "id": instance.id,
            "size_disk": size_disk,
            "size_ram": size_ram,
            "vcpus": instance.full_flavor.vcpus,
            "flavor_id": instance.full_flavor.id
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")'''


class NetworksTable(tables.DataTable):
    tenant_name = tables.Column("tenant_name", 
                            verbose_name=_("Tenant Name"))
    branch_name = tables.Column("branch_name", 
                            verbose_name=_("Branch Name"))
    name = tables.Column("name",
                        link="horizon:project:instances:detail",
                        verbose_name=_("Cloud Gateway Name"))
    image_id = tables.Column("image_id",
                                 verbose_name=_("Image Name"))
    '''ip = tables.Column(get_ips,
                        verbose_name=_("Gateway IP Address"),
                        attrs={'data-type': "ip"})'''
    keypair = tables.Column(get_keyname, verbose_name=_("Key Pair"))
    
    '''def get_object_id(self, network):
        return network['id']
        #return tenant_id

    def get_row_actions(self, datum):
        #self._meta.row_actions = (AddSite, AddGW, DeleteSite, DeleteGW, DeleteNetworks,)
        if datum.status=="CONNECTED":
          self._meta.row_actions = (AddLink, DeleteLink, AddSite, AddGW, GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
        if datum.status=="DISCONNECTED":
          self._meta.row_actions = (PreAddLink, AutoBurst, AddSite, AddGW,  GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
        return super(NetworksTable, self).get_row_actions(datum)'''

    class Meta:
        name = "vpns"
        verbose_name = _("Virtual Private Networks")
        #table_actions = (CreateNetwork, DeleteNetworks, AddSites, )
        #status_columns = ["site_count", "gw_count", "link_count", "bw", "status"]
        row_class = UpdateRow
        #table_actions = (GetBranchVM, CreateNetwork, CreateGateway, )
        table_actions = (CreateGateway, DeleteGateway)
	#row_actions = (PreAddLink, AutoBurst, AddLink, DeleteLink, AddSite, AddGW,  GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
