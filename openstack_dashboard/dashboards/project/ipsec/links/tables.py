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

import logging
import copy

#from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
from django.core import urlresolvers
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django.utils.translation import ugettext as _
from django.template import defaultfilters as filters
from horizon.utils.filters import replace_underscores

from openstack_dashboard import api

#from horizon import api
from horizon import tables

from horizon.tables.actions import FilterAction, LinkAction

import re


LOG = logging.getLogger(__name__)

class DeleteLink(tables.LinkAction):
    name = "deletelink"
    verbose_name = _("Disconnect Link")
    classes = ("ajax-modal", "btn-danger", "btn-delete")
    url= "horizon:project:vpns:deletelink"
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        return urlresolvers.reverse(
            'horizon:project:vpns:deletelink',
            args=[datum.id])


class DelLink(tables.LinkAction):
    name = "dellink"
    verbose_name = _("Disconnect Link")
    classes = ("ajax-modal", "btn-danger", "btn-delete")
    
    def get_link_url(self, datum=None):
        print "++++++++++++++++++++++++++++ datum.id=%s"%datum.id
        vpn_id = self.table.kwargs['vpn_id']
        return urlresolvers.reverse(
            'horizon:project:vpns:links:dellink',
            args=[vpn_id, datum.id])
	

class UpdateRow(tables.Row):
   ajax = True

   def get_data(self, request, obj_id):
	vpn_id = self.table.kwargs['vpn_id']
	link = api.elasticnet.elasticnet_get_link(request, vpn_id, obj_id)
        #enet=api.elasticnet.elasticnet_network_get(request, obj_id)
        print "+++++ vpn_id=%s, obj_id=%s, link result=%s"%(vpn_id, obj_id, link)
        return link


class LinksTable(tables.DataTable):

    STATUS_CHOICES = (
        ("CONNECTED", False),
        ("CONNECTING...", True),
        ("DISCONNECTING...", True),
        ("DISCONNECTED", False),
    )

    id = tables.Column("id", verbose_name=_("Link id"), sortable=True)
    #site1 =  tables.Column("site1", verbose_name=_("Site 1"), sortable=True)
    #site2 =  tables.Column("site2", verbose_name=_("Site 2"), sortable=True)
    gwid1 =  tables.Column("gwid1", verbose_name=_("Gateway 1"), sortable=True)
    gwid2 =  tables.Column("gwid2", verbose_name=_("Gateway 2"), sortable=True)
    bw = tables.Column("bw", verbose_name=_("Commited BW (Kbps)"), sortable=True,   filters=(filters.title,replace_underscores), status=False)
    eir = tables.Column("eir", verbose_name=_("Excess BW - best effort (Kbps)"), sortable=True,   filters=(filters.title,replace_underscores), status=False)
    cbs = tables.Column("cbs", verbose_name=_("Commited Burst (Bytes)"), sortable=True,   filters=(filters.title,replace_underscores), status=False)
    pbs = tables.Column("pbs", verbose_name=_("Peak Burst - best effort (Bytes)"), sortable=True,   filters=(filters.title,replace_underscores), status=False)
    state = tables.Column("state", verbose_name=_("State"), sortable=True,  filters=(filters.title,replace_underscores), status=True,
                           status_choices=STATUS_CHOICES) 

    def get_object_id(self, link):
        return link.id

    def get_row_actions(self, datum):
	if datum.state=="CONNECTED":
          self._meta.row_actions = (DelLink,)
        if datum.state=="DISCONNECTED":
          self._meta.row_actions = ()
        return super(LinksTable, self).get_row_actions(datum)

    class Meta:
        name = "links"
        verbose_name = _("Links")
	status_columns = ["bw", "state"]
	row_class=UpdateRow
        row_actions = (DelLink,)
        table_actions = ( )
	order_by=('bw', 'state')
