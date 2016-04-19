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
import time
import logging
from django.core import urlresolvers
#from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django import template
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
#from django.utils.translation import ugettextG as _

from openstack_dashboard.api import elasticnet
from openstack_dashboard import api
from openstack_dashboard import policy

#from horizon import api
from horizon import tables
from horizon.utils.filters import replace_underscores
from links.tables import DeleteLink
import json
import requests

LOG = logging.getLogger(__name__)

class GetBranchGwVM(tables.LinkAction):
    name = "getbranchgwvm"
    verbose_name = _("Get Branch GW VM")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:getbranchgwvm"
    def get_link_url(self, datum=None):
        print "+++RBA RBA+++++++++++++++++++++++++ datum.id=%s"%datum.id
        urlfromview=reverse(
            'horizon:project:ipsec:getbranchgwvm',
            args=[datum.id])
        print "+++ RBA RBA +++++ url=%s"%urlfromview
        return urlfromview

class GetBranchVM(tables.LinkAction):
    name = "getbranchvm"
    verbose_name = _("Get Branch VM")
    classes = ("ajax-modal", "btn-create")
    url = 'horizon:project:ipsec:getbranchvm'
    def get_link_url(self, datum=None):
        urlfromview=reverse(
	    'horizon:project:ipsec:getbranchvm')
	    #args=[datum.id])
            #'horizon:openstack_dashboard:dashboards:project:ipsec:getbranchvm')
        return shortcuts.redirect(urlfromview)

class AddSite(tables.LinkAction):
    name = "addsite"
    verbose_name = _("Add Site")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:addsite"
    def get_link_url(self, datum=None):
        print "+++RBA RBA+++++++++++++++++++++++++ datum.id=%s"%datum.id
        urlfromview=reverse(
            'horizon:project:ipsec:addsite',
            args=[datum.id])
        print "+++ RBA RBA +++++ url=%s"%urlfromview
        return urlfromview

class AddGW(tables.LinkAction):
    name = "addgw"
    verbose_name = _("Add GW")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:addgw"
    def get_link_url(self, datum=None):
        return urlresolvers.reverse(
            'horizon:project:ipsec:addgw',
            args=[datum.id])

class UpdateRow(tables.Row):
    ajax = True
    def get_data(self, request, obj_id):
        #enet=api.elasticnet.elasticnet_network_get(request, obj_id)
        #return enet
        return 

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
        return shortcuts.redirect('horizon:project:ipsec:index')


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Virtual Private Network")
    url = "horizon:project:ipsec:create"
    classes = ("ajax-modal", "btn-create")

class EstablishVPN(tables.LinkAction):
    name = "estVPN"
    verbose_name = _("VPN Connectivity")
    url = "horizon:project:ipsec:createvpn"
    classes = ("ajax-modal", "btn-create")

'''class DisconnectVPN(tables.DeleteAction):
    name = "Disconnect VPN"
    data_type_singular = _("VPN")
    data_type_plural = _("VPNs")

    def delete(self, request, vpn_id):
        try:
            vpn_url = 'http://127.0.0.1:7007/delete_vpn'
            # Send the delete request.
            payload = {'vpn_id': vpn_id}
            headers = {'content-type': 'application/json'}
            rsp = requests.post(vpn_url, data=json.dumps(payload), headers = headers)
        except Exception:
            msg = _('Failed to delete gateway%s')
            redirect = reverse("horizon:project:vpns:index")
            exceptions.handle(request, msg % vpn_id, redirect=redirect)

    def handle(self, table, request, object_ids):
        # Overriden to show clearer error messages instead of generic message
	url = 'http://127.0.0.1:7007/disconnect_ipsec'
	try:
	    for obj_id in object_ids:
	        payload = {'id':int(obj_id)}
	        headers = {'content-type': 'application/json'}
	        rsp = requests.post(url, data=json.dumps(payload), headers = headers)
	except Exception:
            msg = _('Failed to handle disconnect ipsec')
            redirect = reverse("horizon:project:vpns:index")
            exceptions.handle(request, msg, redirect=redirect)

    def action(self, request, object_id):
        # Overriden to show clearer error messages instead of generic message
	url = 'http://127.0.0.1:7007/disconnect_ipsec'
	#try:
	#    for obj_id in object_ids:
	#        payload = {'id':int(obj_id)}
	#        headers = {'content-type': 'application/json'}
	#        rsp = requests.post(url, data=json.dumps(payload), headers = headers)
	#	time.sleep(2)
	try:
	    payload = {'id':int(object_id)}
	    headers = {'content-type': 'application/json'}
	    rsp = requests.post(url, data=json.dumps(payload), headers = headers)
      	    time.sleep(2)
	except Exception:
            msg = _('Failed to handle disconnect ipsec')
            redirect = reverse("horizon:project:vpns:index")
            exceptions.handle(request, msg, redirect=redirect)'''
   
class DisconnectVPN(policy.PolicyTargetMixin,
                    tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete VPN Connectivity",
            u"Delete VPN Connectivity",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted VPN Connectivities",
            u"Deleted VPN Connectivities",
            count
        )

    policy_rules = (("ipsec", "delete_ipsec"),)

    def delete(self, request, network_id):
        network_name = network_id
	url = 'http://127.0.0.1:7007/disconnect_ipsec'
	try:
            payload = {'id':int(network_id)}
            headers = {'content-type': 'application/json'}
            rsp = requests.post(url, data=json.dumps(payload), headers = headers)
            # Retrieve the network list.
        except Exception:
            msg = _('Failed to delete ipsec %s')
            LOG.info(msg, network_id)
            redirect = reverse("horizon:project:ipsec:index")
            exceptions.handle(request, msg % network_name, redirect=redirect)
 
class PreAddLink(tables.LinkAction):
    name = "preaddlink"
    verbose_name = _("Connect Link")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:preaddlink"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:ipsec:preaddlink',
            args=[datum.id])

class AutoBurst(tables.LinkAction):
    name = "autoburst"
    verbose_name = _("Use for Auto Burst")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:autoburst"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:ipsec:autoburst',
            args=[datum.id])

class AddLink(tables.LinkAction):
    name = "addlink"
    verbose_name = _("Add Link")
    classes = ("ajax-modal", "btn-create")
    url = "horizon:project:ipsec:preaddlink"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:ipsec:preaddlink',
            args=[datum.id])

class RequestBandwidth(tables.LinkAction):
    name = "requestbandwidth"
    verbose_name = _("Request Bandwidth")
    url = "horizon:project:ipsec:reqbw"
    classes = ("ajax-modal", "btn-create")

class DeleteSite(tables.LinkAction):
    name = "deletesite"
    verbose_name = _("Delete Site")
    url = "horizon:project:ipsec:delsite"
    classes = ("ajax-modal", "btn-create")

class DeleteGW(tables.LinkAction):
    name = "deletegw"
    verbose_name = _("Delete GW")
    url = "horizon:project:ipsec:delgw"
    classes = ("ajax-modal", "btn-create")

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

def get_subnets(network):
    template_name = 'project/networks/_network_ips.html'
    context = {"subnets": network.subnets}
    return template.loader.render_to_string(template_name, context)

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
    '''STATUS_CHOICES = (
        ("Connected", True),
        ("Disconnected, Not Monitored", True),
        #("Connecting...", True),
        #("Disconnecting...", True),
        ("Disconnected", True),
    )

    name = tables.Column("name", link='horizon:project:ipsec:links:links',
                         verbose_name=_("VPN Name"))
    id = tables.Column("id", link='horizon:project:ipsec:links:links',
                       verbose_name=_("VPN UUID"))
    vpntype = tables.Column("nettype", verbose_name=_('VPN Type'),
                               empty_value="Not defined")
    site_count = tables.Column("site_count",  link='horizon:project:ipsec:sites:sites', verbose_name=_('Sites'),
                               empty_value="0 sites", filters=(filters.title,replace_underscores), status=True)
    gw_count = tables.Column("gw_count", link='horizon:project:ipsec:gws:gws', verbose_name=_('GWs'),
                               empty_value="0 gws", filters=(filters.title,replace_underscores), status=True)
    #gw_name = tables.Column("gw_name", link="horizon:project:instances:detail", verbose_name=_("GW Instance Name"))
    #gw_ip = tables.Column(get_ips, verbose_name=_("IP Address"), attrs={'data-type': "ip"})
    link_count = tables.Column("link_count",  link='horizon:project:ipsec:links:links', verbose_name=_('Links'),
                               empty_value="0 links", filters=(filters.title,replace_underscores), status=True)
    #branchvm =  tables.Column("branchvm", verbose_name=_("GW VM URL"), link='http://129.192.170.90/branchvpn2ericsson.ova',
    #                           empty_value="http://129.192.170.90/branchvpn2ericsson.ova", filters=(filters.title,replace_underscores), status=True)
    bw = tables.Column("bw", verbose_name=_('Agg BW CIR(Kbps)'),
                               empty_value="0", filters=(filters.title,replace_underscores), status=True)
    status = tables.Column("status",  verbose_name=_('Status'),
                               empty_value="Disconnected", filters=(filters.title,replace_underscores), status=True,  status_choices=STATUS_CHOICES)'''
    id = tables.Column( "id", verbose_name=_("ID"))
    tenant_name = tables.Column("tenant_name", 
                            verbose_name=_("Tenant Name"))
    branch_name = tables.Column("branch_name", 
                            verbose_name=_("Branch Name"))
    vpn_name = tables.Column("vpn_name",
                        link="horizon:project:instances:detail",
                        verbose_name=_("VPN Name"))
    gateway_ip = tables.Column("gateway_ip",
                        verbose_name=_("Cloud Gateway IP Address"))
    branch_ip = tables.Column("branch_ip",
                        verbose_name=_("Branch Gateway IP Address"))
    gateway_subnet = tables.Column("gateway_subnet",
                            verbose_name=_("Cloud Subnet"),)
    branch_subnet = tables.Column("branch_subnet",
                            verbose_name=_("Branch Subnet"),)
    '''image_name = tables.Column("image_name",
                                 verbose_name=_("Image Name"))
    size = tables.Column(get_size,
                        verbose_name=_("Size"),
                        attrs={'data-type': 'size'})
    gateway_ip = tables.Column(get_ips,
                        verbose_name=_("Cloud Gateway IP Address"),
                        attrs={'data-type': "ip"})
    branch_ip = tables.Column(get_ips,
                        verbose_name=_("Branch Gateway IP Address"),
                        attrs={'data-type': "ip"})
    gateway_subnet = tables.Column(get_subnets,
                            verbose_name=_("Cloud Subnet"),)
    branch_subnet = tables.Column(get_subnets,
                            verbose_name=_("Branch Subnet"),)'''
    
    '''def get_object_id(self, network):
        return network['id']
        #return tenant_name

    def get_row_actions(self, datum):
        #self._meta.row_actions = (AddSite, AddGW, DeleteSite, DeleteGW, DeleteNetworks,)
        if datum.status=="CONNECTED":
          self._meta.row_actions = (AddLink, DeleteLink, AddSite, AddGW, GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
        if datum.status=="DISCONNECTED":
          self._meta.row_actions = (PreAddLink, AutoBurst, AddSite, AddGW,  GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
        return super(NetworksTable, self).get_row_actions(datum)'''

    class Meta:
        name = "ipsec"
        verbose_name = _("VPN Connection")
        #table_actions = (CreateNetwork, DeleteNetworks, AddSites, )
        #status_columns = ["site_count", "gw_count", "link_count", "bw", "status"]
        row_class = UpdateRow
        #table_actions = (GetBranchVM, CreateNetwork, CreateGateway, )
        table_actions = (EstablishVPN, DisconnectVPN)
	#row_actions = (PreAddLink, AutoBurst, AddLink, DeleteLink, AddSite, AddGW,  GetBranchGwVM, DeleteSite, DeleteGW, DeleteNetworks,)
