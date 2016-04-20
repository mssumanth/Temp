# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2Cisco Systems Inc.
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

import json
from restful_lib import Connection
import urlparse

from openstack_dashboard.api.base import url_for
from django.core.urlresolvers import reverse
from django import shortcuts
from django.contrib import messages
from django.core import validators
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from openstack_dashboard.api import elasticnet
from openstack_dashboard import api

#from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables

LOG = logging.getLogger(__name__)

import re

class CreateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20",
                           label=_("Elastic Network Name"),
                           validators=[validators.validate_slug],
                           error_messages={'invalid': _('Network names may '
                                'only contain letters, numbers, underscores '
                                'and hyphens.')})
    CHOICES = (('MPLS', 'L2VPN (VPLS)'), ('BGP', 'L3VPN (IPSec)'))
    #vpntype = forms.ChoiceField(widget=forms.RadioSelect, required=True, label='Type', choices=CHOICES)
    vpntype = forms.ChoiceField(required=True, label='VPN Type', choices=CHOICES)
    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def handle(self, request, data):
        try:
            api.elasticnet.elasticnet_network_create(request, data['name'], data['vpntype'])
            messages.success(request, _("Elastic Network created successfully."))
        except:
            exceptions.handle(request, _('Unable to create elastic network.'))
        return shortcuts.redirect(self.success_url)


class UpdateVPN(forms.SelfHandlingForm):
    tenant_name = forms.CharField(label=_("Tenant Name"), required=False)
    id = forms.CharField(label=_("ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    failure_url = 'horizon:project:ipsec:index'

    def handle(self, request, data):
        try:
	    vpns = api.elasticnet.getVPNList(self)
            for vpn in vpns:
                LOG.debug("IPSEC in views: {0}".format(vpn.getInfo()))
            msg = _('Network %s was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return vpns
        except Exception:
	    msg = _('Failed to update network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class AddSite(forms.SelfHandlingForm):
    CHOICES = ( ('LEGACY', 'A legacy non OpenStack Site (for branch office)'), ('OS', 'An OpenStack Site (cloud site)'))
    sitechoice = forms.ChoiceField(required=True, label='Add a Site of type ', choices=CHOICES)
    site_name = forms.CharField(required=False, label=_("Site Name"))
    keystone = forms.CharField(required=False, max_length="20",
                           label=_("Keystone Endpoint (only for OS site)"))
    token = forms.CharField(required=False, max_length="20", widget = forms.HiddenInput())
    user = forms.CharField(required=False, max_length="20",
                           label=_("Username Credential (OS_USERNAME or branch user login)"),
                           validators=[validators.validate_slug],
                           error_messages={'invalid': _('Logins may '
                                'only contain letters, numbers, underscores '
                                'and hyphens.')})
    password = forms.CharField(required=False, label=_("Password Credential (OS_PASSWORD or branch user password)"),
                               widget=forms.PasswordInput(render_value=False))
    tenant = forms.CharField(required=False, label=_("OS_TENANT_NAME or empty for branch user"))
    ip  = forms.CharField(required=False, label=_("public IP address of branch site (non OS)"))
    certificate  = forms.CharField(required=False, label=_("public certificate of branch site (non OS)"), widget=forms.Textarea)

    print "******** sitechoice=%s"%sitechoice
    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def handle(self, request, data):
        print "+++++++RBA RBA RBA +++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/addsite', uri)
        vpn_id = match.group(1)
        try:
            if data['sitechoice'] in ['LEGACY', '']:
		site=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_id+'.'+data['site_name'],  data['keystone'], data['token'], data['user'], data['password'], data['tenant'], data['ip'], data['certificate'])
                messages.success(request, _("Branch Site %s added successfully. you can download the VM image and boot it up to connect...")% vpn_id+'.'+ data['site_name'])
		return shortcuts.redirect("horizon:project:ipsec:index")
            else:
		site=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_id+'.'+data['site_name'],  data['keystone'], data['token'], data['user'], data['password'], data['tenant'])
                messages.success(request, _("OS Cloud Site %s added successfully.")% vpn_id+'.'+ data['site_name'])
		return shortcuts.redirect("horizon:project:ipsec:index")
        except:
	    msg =  _('Failed to update network %s') %  data['sitechoice']
	    LOG.info(msg)
	    redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
	    return False

    def get_context_data(self, **kwargs):
        context = super(AddSiteView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context


class GetBranchGwVM(forms.SelfHandlingForm):
    CHOICES = ( ('LEGACY', 'A legacy non OpenStack Site (for branch office)'), ('OS', 'An OpenStack Site (cloud site)'))
    #certificate  = forms.CharField(required=False, label=_("public certificate of branch site (non OS)"), widget=forms.Textarea)

    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def handle(self, request, data):
        print "+++++++RBA RBA RBA +++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/getbranchgwvm', uri)
        vpn_id = match.group(1)
        try:
		vm=api.elasticnet.getBranchGwVM(request, vpn_id)
                messages.success(request, _("VM image customized for VPN %s ... instantiate it somewhere ... .")% vpn_id)
                #return shortcuts.redirect("horizon:project:ipsec:index")
                return True
        except:
            msg =  _('Failed to generate VM image') 
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False

    def get_context_data(self, **kwargs):
        context = super(GetBranchGwVMView, self).get_context_data(**kwargs)
        context["vpn_id"] = self.kwargs['vpn_id']
        return context

class GetBranchVM(forms.SelfHandlingForm):
    CHOICES = ( ('LEGACY', 'A legacy non OpenStack Site (for branch office)'), ('OS', 'An OpenStack Site (cloud site)'))
    #certificate  = forms.CharField(required=False, label=_("public certificate of branch site (non OS)"), widget=forms.Textarea)

    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def handle(self, request, data):
        print "+++++++RBA RBA RBA +++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        vpn_id = 0
        try:
                vm=api.elasticnet.getBranchGwVM(request, vpn_id)
                messages.success(request, _("VM image customized for VPN %s ... instantiate it somewhere ... .")% vpn_id)
                #return shortcuts.redirect("horizon:project:ipsec:index")
                return True
        except:
            msg =  _('Failed to generate VM image')
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False

class AddGW(forms.SelfHandlingForm):
    SCHOICES = (('cloudA', 'cloudA in San Jose'), ('cloudB', 'cloudB in San Jose'), ('jorvas', 'cloud in Jorvas'))
    GCHOICES = (('cloudA_gw', 'cloud A Gateway 1'), ('cloudB_gw', 'cloud B Gateway 1'), ('jorvas_gw', 'Jorvas cloud Gateway 1'),('new', 'Add a New Gateway'))
    sitechoice = forms.ChoiceField(required=True, label='Choose Site', choices=SCHOICES)
    gwchoice = forms.ChoiceField(required=True, label='Add a Gateway', choices=GCHOICES)
    print "******** sitechoice=%s"%sitechoice
    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/addgw/', uri)
        elasticnet_id = match.group(1)
        try:
            if data['sitechoice'] in ['new', '']:
                print "create a new gw -- not implementned yet"
            else:
                api.elasticnet.elasticnet_add_gw(request, elasticnet_id, data['sitechoice'], data['gwchoice'])
                messages.success(request, _("Gateway added successfully."))
        except:
            exceptions.handle(request, _('Unable to add gateway.'))
        return shortcuts.redirect("horizon:project:ipsec:index")

class CreateGateway(forms.SelfHandlingForm):
    SCHOICES = (('cloudA', 'cloudA in San Jose'), ('cloudB', 'cloudB in San Jose'), ('jorvas', 'cloud in Jorvas'))
    GCHOICES = (('cloudA_gw', 'cloud A Gateway 1'), ('cloudB_gw', 'cloud B Gateway 1'), ('jorvas_gw', 'Jorvas cloud Gateway 1'),('new', 'Add a New Gateway'))
    sitechoice = forms.ChoiceField(required=True, label='Choose Site', choices=SCHOICES)
    gwchoice = forms.ChoiceField(required=True, label='Add a Gateway', choices=GCHOICES)
    print "******** sitechoice=%s"%sitechoice
    success_url= 'horizon:project:ipsec:creategw'
    failure_url= 'horizon:project:ipsec:creategw'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:creategw")

    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/creategw/', uri)
        elasticnet_id = match.group(1)
        try:
            if data['sitechoice'] in ['new', '']:
                print "create a new gw -- not implemented yet"
            else:
                api.elasticnet.elasticnet_add_gw(request, elasticnet_id, data['sitechoice'], data['gwchoice'])
                messages.success(request, _("Gateway added successfully."))
        except:
            exceptions.handle(request, _('Unable to add gateway.'))
        return shortcuts.redirect("horizon:project:ipsec:creategw")



class PreAddLink(forms.SelfHandlingForm):
    p_gw = forms.ChoiceField(required=True, label=_("Link this Provider Gateway (VPN Hub):"))
    e_gw = forms.ChoiceField(required=True, label=_("to your Remote Gateway (VPN Spoke):"))

    p_nets = forms.ChoiceField(required=True, label=_("Stitching this Provider Quantum network:"))
    e_nets = forms.ChoiceField(required=True, label=_("to your Remote Quantum network:"))

    bw = forms.IntegerField(max_value="100000000000",
                               label=_("With this Commited Bandwidth (Kbps)="),
                               validators=[validators.validate_slug],
                               error_messages={'invalid': _('Bandwidth may '
                                               'only contain numbers')})
    eir = forms.IntegerField(max_value="100000000000", initial="0", 
                               label=_("Excess BW in best effort (Kbps)="),
                               validators=[validators.validate_slug],
                               error_messages={'invalid': _('Bandwidth may '
                                               'only contain numbers')})
    cbs = forms.IntegerField(max_value="100000000000", initial="0",
                               label=_("Commited Burst Size (Bytes)="),
                               validators=[validators.validate_slug],
                               error_messages={'invalid': _('Bandwidth may '
                                               'only contain numbers')})
    pbs = forms.IntegerField(max_value="100000000000", initial="0",
                               label=_("Peak Burst Size in best effort (Bytes)="),
                               validators=[validators.validate_slug],
                               error_messages={'invalid': _('Bandwidth may '
                                               'only contain numbers')})


    p_tk=''
    e_tk=''
    p_site=''
    e_site=''
    success_url= 'horizon:project:ipsec:addlink'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:addlink")

    def __init__(self, request, *args, **kwargs):
        super(PreAddLink, self).__init__(request, *args, **kwargs)

	# get vpn_id
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/preaddlink/', uri)
        vpn_id = match.group(1)

	# get gateways
        gws = []
        try:
            gws = api.elasticnet.elasticnet_list_gws(self.request, vpn_id)
        except Exception as e:
            msg = _('Failed to get gateways list %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url,
                               args=[request.REQUEST['vpn_id']])
            exceptions.handle(request, msg, redirect=redirect)

	c1=()
	c2=()
	for gw in gws:
	   s1=str(gw.name)
	   s2=str(gw.id)
	   if "Provider" in s2:
	     c1=c1+((s1, s2),)
	   else:
	     c2=c2+((s1, s2),)
        self.fields['p_gw'].choices = c1
        self.fields['e_gw'].choices = c2

	# get provider networks
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/preaddlink/', uri)
        vpn_id = match.group(1)

        pnets = api.quantum.network_list(request)

        d1=()
        for pnet in pnets:
           s1=str(pnet.id)
           s2=str(pnet.name+':vlan'+str(pnet.provider__segmentation_id)+':'+pnet.id)
           d1=d1+((s1, s2),)
        self.fields['p_nets'].choices = d1

        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/preaddlink/', uri)
        vpn_id = match.group(1)

	# get enterprise networks and servers (to choose what to burst)	
        # get the site from the gw
        psites=[]
        esites=[]
        for gw in gws:
           g=str(gw.id)
           gsplit=re.split(r'\.',g)
           if "Provider" in g:
             psites.append(gsplit[0]+'.'+gsplit[1])
           else:
             esites.append(gsplit[0]+'.'+gsplit[1])
        # get the token (or generate one) from the site credentials, then get the networks from the last added site (all sites has to be added and filter nets of one selected in form)
        for esite in esites:
          site= api.elasticnet.elasticnet_get_site(self.request, vpn_id, esite)
          #enets= api.elasticnet.elasticnet_get_networks_in_site(request, vpn_id, esite)
          tokenObject = api.elasticnet.elasticnet_get_token_in_site(request, vpn_id, esite)
          self.e_tk = tokenObject['id']
          print "!!! !!! type ="+str(tokenObject['id'])
          enets = api.elasticnet.elasticnet_get_networks_in_site(request, vpn_id, site.keystone, self.e_tk)
        d2=()
        for enet in enets:
           s1=str(enet['id'])
           s2=str(enet['name']+':vlan'+str(enet['provider:segmentation_id'])+':'+enet['id'])
           d2=d2+((s1, s2),)
        self.fields['e_nets'].choices = d2

	
 
    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/preaddlink/', uri)
        vpn_id = match.group(1)
        print "++++++++++++ ////////////// RBA RBA vpn_id = %s"%vpn_id

	self.p_tk=request.user.token.id
	try:
        	messages.success(request, _("Link in process of establishement... Pushing low level network configuration..."))
		pgsplit=re.split(r'\.',str(data['p_gw']))
		self.p_site=pgsplit[0]+'.'+pgsplit[1]
        	egsplit=re.split(r'\.',str(data['e_gw']))
        	self.e_site=egsplit[0]+'.'+egsplit[1]

	        print "++++++ data to plugin : vpn=%s, psite=%s, pgw=%s, pnets=%s, ptk=%s, esite=%s, egw=%s, enets=%s, etk=%s, bw=%s"%(vpn_id, self.p_site, data['p_gw'] , data['p_nets'], 
		   self.p_tk, self.e_site, data['e_gw'] , data['e_nets'], self.e_tk, data['bw'])
		
		# should use a modular client below once it supports complex jsons: 
		#api.elasticnet.elasticnet_add_link(request, vpn_id, self.p_site, str(data['p_gw']) , str(data['p_nets']), self.p_tk, self.e_site, str(data['e_gw']) , str(data['e_nets']), self.e_tk, str(data['bw']))
		if str(request.user.username).startswith("acme"):
		  o = urlparse.urlparse(url_for(request, "ipsecvpn"))
		else:
		  o = urlparse.urlparse(url_for(request, "vpn"))

		conn0 = Connection("http://"+str(o.hostname)+":9797", "ericsson", "ericsson")
	        uri0 = "/v1.0/tenants/acme/networks/"+str(vpn_id)+"/links.json"
                LOG.debug("http://"+str(o.hostname)+":9797")
                LOG.debug(uri0)
                header = {}
                header["Content-Type"]= "application/json"
                jsonbody='{"sites": [{"id":"'+str(self.p_site)+'", "gateway":"'+ str(data['p_gw']) +'", "network":"'+  str(data['p_nets']) +'", "token_id":"'+str(self.p_tk)+ '"}, {"id":"' \
		  + str(self.e_site)+'", "gateway":"'+ str(data['e_gw']) +'", "network":"'+  str(data['e_nets']) +'", "token_id":"'+str(self.e_tk)+ '"}], "qos":{"bandwidth":"' \
		  + str(data['bw'])+'", "eir":"'+ str(data['eir'])+ '", "cbs":"'+ str(data['cbs'])+ '", "pbs":"'+ str(data['pbs'])+ '"}}'
                print "+++ ewan result json body =%s"%jsonbody
                result=conn0.request_post(uri0, body=jsonbody, headers=header)
                print "+++ ewan result body =%s"%result["body"]
                body=json.loads(result["body"])
                print "+++ewan body=%s"%body
                linkid=str(body['link']['id'])
                print "+++ewan linkid=%s"%linkid

                messages.success(request, _("Link added successfully."))
		shortcuts.redirect("horizon:project:ipsec:index")
		return True
        except Exception as e:
	    msg = _('Failed to authorize Link from remote Enterprise Site crendentials : %s') % e.message
            LOG.info(msg)
	    return shortcuts.redirect("horizon:project:ipsec:index")





class AutoBurst(forms.SelfHandlingForm):
    e_servers = forms.ChoiceField(required=True, label=_("Autoburst this remote server here:"))

    sla = forms.IntegerField(max_value="10",
                               label=_("within a time constraint of (s):"),
                               validators=[validators.validate_slug])
    th = forms.IntegerField(max_value="100", initial="90",
                               label=_("* once its avg load is higher than the threshold (%):"),
                               validators=[validators.validate_slug])
    time = forms.IntegerField(max_value="100",initial="10",
                               label=_("* during a period of time (s):"),
                               validators=[validators.validate_slug])
                               
    p_gw = forms.ChoiceField(required=True, label=_("Over an elastic WAN Link from:"))
    e_gw = forms.ChoiceField(required=True, label=_("to your Remote Gateway (VPN Spoke):"))

    p_nets = forms.ChoiceField(required=True, label=_("Stitching this Provider Quantum network:"))
    e_nets = forms.ChoiceField(required=True, label=_("to your Remote Quantum network:"))


    eir =''
    cbs =''
    pbs =''
    p_tk=''
    e_tk=''
    p_site=''
    e_site=''
    vmtenantid=''
    success_url= 'horizon:project:ipsec:index'
    failure_url= 'horizon:project:ipsec:index'

    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def __init__(self, request, *args, **kwargs):
        super(AutoBurst, self).__init__(request, *args, **kwargs)
        # get vpn_id
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/autoburst/', uri)
        vpn_id = match.group(1)

        # get gateways
        gws = []
        try:
            gws = api.elasticnet.elasticnet_list_gws(self.request, vpn_id)
        except Exception as e:
            msg = _('Failed to get gateways list %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url,
                               args=[request.REQUEST['vpn_id']])
            exceptions.handle(request, msg, redirect=redirect)

        c1=()
        c2=()
        for gw in gws:
           s1=str(gw.name)
           s2=str(gw.id)
           if "Provider" in s2:
             c1=c1+((s1, s2),)
           else:
             c2=c2+((s1, s2),)
        self.fields['p_gw'].choices = c1
        self.fields['e_gw'].choices = c2

        # get provider networks
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/autoburst/', uri)
        vpn_id = match.group(1)

        pnets = api.quantum.network_list(request)

        d1=()
        for pnet in pnets:
           s1=str(pnet.id)
           s2=str(pnet.name+':vlan'+str(pnet.provider__segmentation_id)+':'+pnet.id)
           d1=d1+((s1, s2),)
        self.fields['p_nets'].choices = d1

        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/autoburst/', uri)
        vpn_id = match.group(1)

        # get enterprise networks and servers (to choose what to burst)
        # get the site from the gw
        psites=[]
        esites=[]
        for gw in gws:
           g=str(gw.id)
           gsplit=re.split(r'\.',g)
           if "Provider" in g:
             psites.append(gsplit[0]+'.'+gsplit[1])
           else:
             esites.append(gsplit[0]+'.'+gsplit[1])
        # get the token (or generate one) from the site credentials, then get the networks from the last added site (all sites has to be added and filter nets of one selected in form)
        for esite in esites:
          site= api.elasticnet.elasticnet_get_site(self.request, vpn_id, esite)
          #enets= api.elasticnet.elasticnet_get_networks_in_site(request, vpn_id, esite)
          tokenObject = api.elasticnet.elasticnet_get_token_in_site(request, vpn_id, esite)
          #print "!!! !!! toeknobj="+tokenObject
          self.e_tk = tokenObject['id']
          enets = api.elasticnet.elasticnet_get_networks_in_site(request, vpn_id, site.keystone, self.e_tk)
          eservers = api.elasticnet.elasticnet_get_servers_in_site(request, vpn_id, site.keystone, self.e_tk, tokenObject['tenant']['id'])
	  self.vmtenantid=tokenObject['tenant']['id']
        d2=()
        for enet in enets:
           s1=str(enet['id'])
           s2=str(enet['name']+':vlan'+str(enet['provider:segmentation_id'])+':'+enet['id'])
           d2=d2+((s1, s2),)
        self.fields['e_nets'].choices = d2
	d3=()
	for eserver in eservers:
	   s1=str(eserver['id'])
	   s2=str(eserver['name']+' uuid:'+s1)
	   d3=d3+((s1, s2),)
	self.fields['e_servers'].choices = d3




    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/ipsec/([^/]+)/autoburst/', uri)
        vpn_id = match.group(1)
        print "++++++++++++ ////////////// RBA RBA vpn_id = %s"%vpn_id


        self.p_tk=request.user.token.id
        try:
                messages.success(request, _("AutoBurst is enabled on the remote VMs using this elastic wan..."))
                pgsplit=re.split(r'\.',str(data['p_gw']))
                self.p_site=pgsplit[0]+'.'+pgsplit[1]
                egsplit=re.split(r'\.',str(data['e_gw']))
                self.e_site=egsplit[0]+'.'+egsplit[1]

                # should use a modular client below once it supports complex jsons:
                #api.elasticnet.elasticnet_add_link(request, vpn_id, self.p_site, str(data['p_gw']) , str(data['p_nets']), self.p_tk, self.e_site, str(data['e_gw']) , str(data['e_nets']), self.e_tk, str(data['bw']))
                if str(request.user.username).startswith("acme"):
                  o = urlparse.urlparse(url_for(request, "ipsecvpn"))
                else:
                  o = urlparse.urlparse(url_for(request, "vpn"))


                conn0 = Connection("http://"+str(o.hostname)+":9797", "ericsson", "ericsson")
                uri0 = "/v1.0/tenants/acme/networks/"+str(vpn_id)+"/links.json"
                LOG.debug("http://"+str(o.hostname)+":9797")
                LOG.debug(uri0)
		bw=None
                header = {}
                header["Content-Type"]= "application/json"
                jsonbody='{"sites": [{"id":"'+str(self.p_site)+'", "gateway":"'+ str(data['p_gw']) +'", "network":"'+  str(data['p_nets']) +'", "token_id":"'+str(self.p_tk)+ '"}, {"id":"' \
                  + str(self.e_site)+'", "gateway":"'+ str(data['e_gw']) +'", "network":"'+  str(data['e_nets']) +'", "token_id":"'+str(self.e_tk)+ '"}], "qos":{"bandwidth":"' \
                  + str(bw)+'"}, "usecase":{"action":"autoburst", "vmuuid":"' \
		  + str(data['e_servers'])+'", "vmtenantid":"'+str(self.vmtenantid)+'", "vmsla":"'+str(data['sla'])+'"}}'
                print "+++ ewan result json body =%s"%jsonbody
                result=conn0.request_post(uri0, body=jsonbody, headers=header)
                print "+++ ewan result body =%s"%result["body"]
                body=json.loads(result["body"])
                print "+++ewan body=%s"%body
                linkid=str(body['link']['id'])
                print "+++ewan linkid=%s"%linkid

                messages.success(request, _("Link added successfully."))
                shortcuts.redirect("horizon:project:ipsec:index")
                return True
        except Exception as e:
            msg = _('Failed to authorize Link from remote Enterprise Site crendentials : %s') % e.message
            LOG.info(msg)
            return shortcuts.redirect("horizon:project:ipsec:index")



