# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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
import netaddr

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows
from horizon.utils import fields

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class CreateLinkInfoAction(workflows.Action):
    GCHOICES1 = (('cloudA_gw', 'cloud A Gateway 1'), ('cloudB_gw', 'cloud B Gateway 1'), ('jorvas_gw', 'Jorvas cloud Gateway 1'))
    GCHOICES2 = (('cloudA_gw', 'cloud A Gateway 1'), ('cloudB_gw', 'cloud B Gateway 1'), ('jorvas_gw', 'Jorvas cloud Gateway 1'))
    gwchoice1 = forms.ChoiceField(required=True, label='Link gateway:', choices=GCHOICES1)
    gwchoice2 = forms.ChoiceField(required=True, label='to gateway:', choices=GCHOICES2)
    bw = forms.IntegerField(max_value="100000000000",
                              label=_("Requested Bandwidth"),
                              validators=[validators.validate_slug],
                              error_messages={'invalid': _('Bandwidth may '
                                              'only contain numbers')})

    def handle(self, request, data):
        print "++++++++++++ ////////////// data = %s"%data
        uri = request.get_full_path()
        match = re.search('/project/vpns/([^/]+)/addlink/', uri)
        elasticnet_id = match.group(1)
        try:
            if data['gwchoice1'] in ['new', '']:
                print "create a new gw -- not implementned yet"
            else:
                api.elasticnet.elasticnet_add_link(request, elasticnet_id, data['gwchoice1'], data['gwchoice2'], data['bw'])
                messages.success(request, _("Link added successfully."))
        except:
            exceptions.handle(request, _('Unable to add link.'))
        #return shortcuts.redirect("horizon:project:vpns:links:links", elasticnet_id=elasticnet_id)
        return shortcuts.redirect("horizon:project:vpns:index")


    CHOICES = (('L2VPN', 'L2VPN (over Fiber, MetroEthernet, VPLS, MPLS, L3/GRE/L2TP, SSL)'), ('L3VPN', 'L3VPN (over Fiber, MetroEthernet, VPLS, MPLS, L3/GRE/L2TP, SSL)'))
    #vpntype = forms.ChoiceField(widget=forms.RadioSelect, required=True, label='Type', choices=CHOICES)
    vpntype = forms.ChoiceField(required=True, label='VPN Type', choices=CHOICES)

    net_name = forms.CharField(max_length=255,
                               label=_("VPN Name"),
                               help_text=_("VPN Name. This field is "
                                           "optional."),
                               required=False)
    private = forms.BooleanField(label=_("Private to this tenant (Isolated from other tenants)"),
                                     initial=True, required=False)

    class Meta:
        name = ("VPN")
        help_text = _("From here you can create a new VPN from a Provider Site to your Enterprise Site.\n"
                      "A Provider Site and your Enterprise Site associated with this VPN "
                      "can be add in the next panel. All Enterprise Sites require to run OpenStack with a reacheable Keystone v2 Service.")


class CreateVPNInfo(workflows.Step):
    action_class = CreateVPNInfoAction
    contributes = ("vpntype", "net_name", "private")


class CreateSiteInfoAction(workflows.Action):
    with_site = forms.BooleanField(label=_("Add your Enterprise Site (below) to this VPN"),
                                     initial=True, required=False)
    CHOICES = (('Data_Center_San_Jose_B', 'Enterprise Data Center in San Jose B'), ('Data_Center_Jorvas', 'Enterprise Data Center in Jorvas'))

    sitechoice = forms.ChoiceField(required=False, label='Existent Enterprise Site', choices=CHOICES)
 
    site_name = forms.CharField(max_length=255,
                                  label=_("If your Enterprise Site (running the VPN agent with chosen VPN type) does not appear, add its config:"),
                                  help_text=_("Enterprise Site Name. This field is "
                                           "optional."),
                                  required=False)
    remote_keystone_endpoint = fields.IPField(label=_("Enterprise Keystone v2 IP address (Port 5000)"),
                          required=False,
                          initial="10.126.71.249",
                          help_text=_("Enterprise Keystone Network address in IPv4 or IPv6 address format "
                                      "(e.g. 192.168.0.0)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=False)
#    ip_version = forms.ChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
#                                   label=_("Keystone server IP Version"))
    remote_login = forms.CharField(max_length=255,
                                  label=_("User LOGIN in Enterprise site"),
                                  help_text=_("Tenant's user LOGIN in Enterprise site. In case you do not want to provide a 24hours expiration token from your Enterprise Keystone "
                                        "each time you connect your VPN. This field is "
                                           "optional."),
                                  required=False)
    remote_tenant = forms.CharField(label=_("Tenant NAME in Enterprise"),
				  help_text=_("Tenant's NAME in Enterprise site. This field is "
                                           "optional."), required=False) 
 #                              widget=forms.PasswordInput(render_value=False), required=False)
    add_local_site = forms.BooleanField(label=_("Add this Provider Site to this VPN"),
                                 help_text=_("Other Sites for this Provider are in other Availability Zones"),
                                    initial=True, required=False)

    class Meta:
        name = ("Provider and Enterprise Sites")
        help_text = _('You can add a Provider Site as well as your Enterprise Site associated with the new '
                      'VPN, in which case "Enterprise Keystone IP address and user credentials" must be '
                      'specified. If you wish to create a vpn WITHOUT adding sites, '
                      ' uncheck the "Add Site" top and bottom checkboxes.')

    def _check_site_data(self, cleaned_data, is_create=True):
        rke = cleaned_data.get('remote_keystone_endpoint')
        ws = cleaned_data.get('with_site')
        #ip_version = int(cleaned_data.get('ip_version'))
        als = cleaned_data.get('add_local_site')
	sn= cleaned_data.get('site_name')
	rl= cleaned_data.get('remote_login')
	rp= cleaned_data.get('remote_tenant')

        if not rke:
            msg = _('Specify "Enterprise Keystone IP Address" or '
                    'clear "Add your Enterprise Site to this VPN" checkbox.')
            raise forms.ValidationError(msg)
        if rke:
            site = netaddr.IPNetwork(rke)
        #    if site.version != ip_version:
        #        msg = _('Keystone IP Address and IP version are inconsistent.')
        #        raise forms.ValidationError(msg)
        if not als and ws:
            msg = _('Make sure you added a Provider Site for the Enterprise Site '
                    'Check "Add this local Provider Site to this VPN in the bottom".')
            raise forms.ValidationError(msg)
	if sn and not rke:
	    msg = _('Make sure you added a keystone endpoint for you newly added site')
            raise forms.ValidationError(msg)
	if rl and not rp:
	    msg = _('Make sure you added a password for the login your provided (we do not store it)')
            raise forms.ValidationError(msg)

    def clean(self):
        cleaned_data = super(CreateSiteInfoAction, self).clean()
        with_site = cleaned_data.get('with_site')
        if not with_site:
            return cleaned_data
        self._check_site_data(cleaned_data)
        return cleaned_data


class CreateSiteInfo(workflows.Step):
    action_class = CreateSiteInfoAction
    contributes = ("with_site", "sitechoice", "site_name", "remote_keystone_endpoint", "remote_login", "remote_tenant", 
                   "add_local_site")


class CreateSiteDetailAction(workflows.Action):
    with_gw = forms.BooleanField(label=_("Add your Enterprise Gateway to this VPN"),
                                     initial=True, required=False)
    #LGCHOICES = (('Provider_AZ1_GW1', 'Cloud Provider Avail. Zone 1 - Gateway 1'), ('Provider_AZ2_GW1', 'Cloud Provider Avail. Zone 2 - Gateway 1'), ('Provider_AZ2_GW2', 'Cloud Provider Avail. Zone 2 - Gateway 2'), ('new', 'Add a New Gateway'))
    RGCHOICES = (('GW1_Data_Center_San_Jose_B', 'Enterprise Data Center in San Jose B  - Gateway 1'), ('GW1_Data_Center_Jorvas', 'Enterprise Data Center in Jorvas - Gateway 1'),('new', 'Add a New Gateway'))
#    lgwchoice = forms.ChoiceField(required=True, label='Add a Provider Gateway', choices=LGCHOICES)
    rgwchoice = forms.ChoiceField(required=True, label='PreConfigured Enterprise Gateway', choices=RGCHOICES)
    gw_name = forms.CharField(max_length=255,
                                  label=_("If your Enterprise Gateway (managed by a VPN agent with chosen VPN type) does not appear, add it:"),
                                  help_text=_("Enterprise Gateway Name. This field is "
                                           "optional."),
                                  required=False)
    gw_endpoint = fields.IPField(label=_("Enterprise Gateway Mgmt IP address (default mgmt port)"),
                          required=False,
                          initial="10.126.70.70",
                          help_text=_("Enterprise Gateway Network address in IPv4 or IPv6 address format "
                                      "(e.g. 192.168.0.0)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=False)

    auto_gw = forms.BooleanField(label=_("AutoDiscover/Choose GWs in Cloud Provider Avail. Zone 1"),
                                     initial=True, required=False)

    class Meta:
        name = ("Provider and Enterprise Gateways")
        help_text = _('You can specify the Provider and Enterprise Gateways in Provider and Enterprise Sites resp. to add to this VPN.')

    def clean(self):
        cleaned_data = super(CreateSiteDetailAction, self).clean()
        return cleaned_data


class CreateSiteDetail(workflows.Step):
    action_class = CreateSiteDetailAction
    contributes = ("with_gw", "rgwchoice", "gw_name", "gw_endpoint", "auto_gw")


class CreateLink(workflows.Workflow):
    slug = "create_link"
    name = _("Create a Link")
    finalize_button_name = _("Create")
    success_message = _('Created link "%s".')
    failure_message = _('Unable to create link "%s".')
    default_steps = (CreateLinkInfo,
                     CreateSiteInfo,
                     CreateSiteDetail)

    def clean(self, sentence):
	return sentence.replace(" ", "")
	
    def get_success_url(self):
        return reverse("horizon:project:vpns:index")

    def get_failure_url(self):
        return reverse("horizon:project:vpns:index")

    def format_status_message(self, message):
        name = self.context.get('net_name') or self.context.get('net_id', '')
        return message % name

    def _create_vpn(self, request, data):
        try:
            vpn=api.elasticnet.elasticnet_network_create(request, self.clean(data['net_name']), data['vpntype'])
            messages.success(request, _("VPN created successfully."))
	    return vpn
        except:
            exceptions.handle(request, _('Unable to create VPN.'))
        return shortcuts.redirect(self.success_url)

    def _add_sites(self, request, data, vpn=None, tenant_id=None,
                       no_redirect=False):
        if vpn:
            vpn_id = vpn['vpn']['id']
	    vpn_name = self.clean(data['net_name'])
        else:
            vpn_id = self.context.get('vpn_id')
	    vpn_name = self.context.get('vpn_name')
        try:
	    if data['add_local_site']:
		lsite=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.Provider_AZ1')
                messages.success(request, _("Local Provider Site %s added successfully.")% vpn_name+'.Provider_AZ1')
            if data['site_name']:
		#remote_keystone_endpoint, remote_login, remote_password
		site=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.'+ self.clean(data['site_name']))
		messages.success(request, _("Enterprise Site %s added successfully.")% vpn_name+'.'+ self.clean(data['site_name']))
            else:
                site=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.'+data['sitechoice'])
                messages.success(request, _("Enterprise Site %s added successfully.")% vpn_name+'.'+data['sitechoice'])
	    return site
        except Exception as e:
            if no_redirect:
                redirect = None
            else:
                redirect = self.get_failure_url()
            exceptions.handle(request,
                              "Failed to add site %s because %s"%(data['sitechoice'], e),
                              redirect=redirect)
            return False

    def _add_gws(self, request, data, vpn=None, tenant_id=None,
                       no_redirect=False):
	if vpn:
            vpn_id = vpn['vpn']['id']
            vpn_name = self.clean(data['net_name'])
        else:
            vpn_id = self.context.get('vpn_id')
            vpn_name = self.context.get('vpn_name')
	rgw=None
	try:
            if data['sitechoice'] in ['new', '']:
                print "create a new gw -- not implemented yet"
            else:
		# auto discover is not implemented yet, so choose one first gw in provider site
                lgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.Provider_AZ1', vpn_name+'.Provider_AZ1.GW1')
		if data['site_name']:
		  if data['gw_name']:
                    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+self.clean(data['site_name']), vpn_name+'.'+ self.clean(data['site_name'])+'.'+ self.clean(data['gw_name']))
		  else:
		    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+self.clean(data['site_name']), vpn_name+'.'+ self.clean(data['site_name'])+'.'+data['rgwchoice'])
		else:
		  if data['gw_name']:
                    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+data['sitechoice'], vpn_name+'.'+data['sitechoice']+'.'+  self.clean(data['gw_name']))
		  else:
		    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+data['sitechoice'], vpn_name+'.'+data['sitechoice']+'.'+data['rgwchoice'])
                messages.success(request, _("Gateways added successfully."))
	    return rgw
        except Exception as e:
            if no_redirect:
                redirect = None
            else:
                redirect = self.get_failure_url()
            exceptions.handle(request,
                              "Failed to add gw %s because %s"%(data['rgwchoice'], e),
                              redirect=redirect)
            return False


    def _delete_vpn(self, request, vpn):
        """Delete the created network when site creation failed"""
        try:
            #api.quantum.network_delete(request, network.id)
            msg = _('Delete the created VPN "%s" '
                    'due to site addition failure.') % vpn_name
            LOG.debug(msg)
            redirect = self.get_failure_url()
            messages.info(request, msg)
            raise exceptions.Http302(redirect)
            #return exceptions.RecoverableError
        except:
            msg = _('Failed to delete VPN %s') % vpn_id
            LOG.info(msg)
            redirect = self.get_failure_url()
            exceptions.handle(request, msg, redirect=redirect)

    def handle(self, request, data):
        vpn = self._create_vpn(request, data)
        if not vpn:
            return False
        # If we do not need to add a site, return here.
        if not data['with_site']:
            return True
        sites = self._add_sites(request, data, vpn, no_redirect=True)
        if sites:
	    if not data['with_gw']:
            	return True
	    self._add_gws(request, data, vpn, no_redirect=True)
            return True
        else:
            self._delete_vpn(request, vpn)
            return False
