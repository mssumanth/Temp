# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from django import shortcuts
from django.contrib import messages
from django.core import validators
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from openstack_dashboard import api

#from horizon import api
from horizon import exceptions
from horizon import forms

import re
import pprint

LOG = logging.getLogger(__name__)

from django.core.urlresolvers import reverse



class DeleteLink(forms.SelfHandlingForm):
    GCHOICES1 = (('yes', 'yes'), ('no', 'no'))
    gwchoice1 = forms.ChoiceField(required=True, label='You need to choose which link you need to disconnect.', choices=GCHOICES1)
    vpn_id=''

    def __init__(self, request, *args, **kwargs):
        super(DeleteLink, self).__init__(request, *args, **kwargs)
	uri = request.get_full_path()
        match = re.search('/project/vpns/([^/]+)/deletelink/', uri)
        self.vpn_id = match.group(1)


    def get_success_url(self):
        print "++++++++++++ //////////////  success ur l +++++++++++++++++++++++++++++"
        return reverse("horizon:project:vpns:links:links",  vpn_id=self.vpn_id)


    def handle(self, request, data):
        print "++++++++++++ ////////////// request = %s"%request
        uri = request.get_full_path()
        match = re.search('/project/vpns/([^/]+)/deletelink/', uri)
        vpn_id = match.group(1)
        #return shortcuts.redirect("horizon:project:vpns:links:links", vpn_id=vpn_id)
        return shortcuts.redirect("horizon:project:vpns:links:links", vpn_id=vpn_id, safe=False)

    
class DelLink(forms.SelfHandlingForm):
    GCHOICES1 = (('yes', 'yes'), ('no', 'no'))
    gwchoice1 = forms.ChoiceField(required=True, label='Are you sure you want to disconnect that link?', choices=GCHOICES1)

    def __init__(self, request, *args, **kwargs):
        super(DelLink, self).__init__(request, *args, **kwargs)
        uri = request.get_full_path()
        match = re.search('/project/vpns/links/([^/]+)/([^/]+)/dellink/', uri)
        self.vpn_id = match.group(1)
        self.link_id =  match.group(2)

    def get_success_url(self):
	vpn_id = self.table.kwargs['vpn_id']
        redirect = reverse('horizon:project:vpns:links:links',
                               args=[vpn_id])
	return redirect

    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/vpns/links/([^/]+)/([^/]+)/dellink/', uri)
        vpn_id = match.group(1)
	link_id =  match.group(2)

        try:
	   if data['gwchoice1']=='yes':
                messages.success(request, _("Deprovisioning Link in process....."))
                api.elasticnet.elasticnet_update_link(request, vpn_id, link_id,  state='DISCONNECTING')
	   	return True
	   else:
		return False
        except Exception as e:
            msg = (_('Failed to deprovision link "%(sub)s": '
                     ' %(reason)s') %
                   {"sub": link_id, "reason": e})
            LOG.info(msg)
            #vpn_id = self.table.kwargs['vpn_id']
            redirect = reverse('horizon:project:vpns:links:links',
                               args=[vpn_id])
            exceptions.handle(request, msg, redirect=redirect)
