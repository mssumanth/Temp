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

from django.core.urlresolvers import reverse

#from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
#from django.core import urlresolvers
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django.utils.translation import ugettext as _

from openstack_dashboard import api

#from horizon import api
from horizon import tables

from horizon.utils.filters import replace_underscores

from horizon.tables.actions import FilterAction, LinkAction
from django.template import defaultfilters as filters
import re


LOG = logging.getLogger(__name__)

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

class SitesTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_("Site id"), sortable=True)
    name =  tables.Column("name", verbose_name=_("Name"), sortable=True)
    keystone =  tables.Column("keystone", verbose_name=_("Keystone"), sortable=True)
    tenant =  tables.Column("tenant", verbose_name=_("Tenant"), sortable=True)
    ip =  tables.Column("ip", verbose_name=_("Public IP@"), sortable=True)
    certificate =  tables.Column("certificate", verbose_name=_("Public certificate"), sortable=True)
    branchvm =  tables.Column("branchvm", verbose_name=_("VPN GW VM URL"), link='http://129.192.170.90/branchvpn2ericsson.ova', 
                               empty_value="http://129.192.170.90/branchvpn2ericsson.ova", filters=(filters.title,replace_underscores), status=True)
 #   state = tables.Column("state", verbose_name=_("State"), sortable=True)

    def get_object_id(self, site):
        return site.id

    def get_row_actions(self, datum):
        self._meta.row_actions = []
        self._meta.row_actions.append(DeleteSite)
        return super(SitesTable, self).get_row_actions(datum)

    class Meta:
        name = "sites"
        verbose_name = _("Sites")
        row_actions = (DeleteSite,)
        table_actions = ( )
