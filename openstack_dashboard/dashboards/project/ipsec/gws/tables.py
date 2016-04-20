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

from openstack_dashboard import api

#from horizon import api
from horizon import tables

from horizon.tables.actions import FilterAction, LinkAction

import re


LOG = logging.getLogger(__name__)

class RequestBandwidth(tables.LinkAction):
    name = "requestbandwidth"
    verbose_name = _("Request Bandwidth")
    url = "horizon:project:vpns:reqbw"
    classes = ("ajax-modal", "btn-create")

class DeleteGW(tables.LinkAction):
    name = "deletegw"
    verbose_name = _("Delete GW")
    url = "horizon:project:vpns:delgw"
    classes = ("ajax-modal", "btn-create")


class GWsTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_("GW id"), sortable=True)
    name =  tables.Column("name", verbose_name=_("Name"), sortable=True)
    site =  tables.Column("site", verbose_name=_("Site"), sortable=True)
    #state = tables.Column("state", verbose_name=_("State"), sortable=True)

    def get_object_id(self, gw):
        return gw.id

    def get_row_actions(self, datum):
        self._meta.row_actions = []
        self._meta.row_actions.append(DeleteGW)
        return super(GWsTable, self).get_row_actions(datum)

    class Meta:
        name = "gws"
        verbose_name = _("Gateways")
        row_actions = (DeleteGW,)
        table_actions = ( )
