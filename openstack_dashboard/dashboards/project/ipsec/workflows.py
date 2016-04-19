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
import urlparse
import random
import requests
import json
from openstack_dashboard.api.base import APIDictWrapper, url_for

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django import shortcuts
from django.template.defaultfilters import filesizeformat  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows
from horizon.forms import fields
from horizon.utils import functions
from horizon.utils import memoized
from horizon.utils import validators

from openstack_dashboard import api
from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils

LOG = logging.getLogger(__name__)
INSTANCE_SEC_GROUP_SLUG = "update_security_groups"

class CreateVPNInfoAction(workflows.Action):
    CHOICES = (('L2VPN', 'L3VPN plugin'), ('L3VPN', 'L3VPN (plugin not implemented)'))
    vpntype = forms.ChoiceField(required=True, label='VPN Type', choices=CHOICES)


    net_name = forms.CharField(max_length=255,
                               label=_("VPN Name"),
                               help_text=_("VPN Name. This field is "
                                           "optional."),
                               required=False)

    private_network = forms.MultipleChoiceField(label=_("Private Networks to Connect to (Note: only non-Shared networks can be connected to by this VPN)"),
                                        required=True,
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Connect VPN to this private network"))
    
    private = forms.BooleanField(label=_("Private to this tenant (Isolated from other tenants)"), initial=True, required=False)


    class Meta:
        name = ("VPN")
        permissions = ('openstack.services.network',)
        help_text = _("From here you can create a new VPN from a Cloud Site to your Enterprise Branch Site.\n"
                      "A Provider Site and your Enterprise Site associated with this VPN "
                      "can be add in the next panel. All Enterprise Sites require to run OpenStack with a reacheable Keystone v2 Service.")

    def populate_private_network_choices(self, request, context):
        try:
            tenant_name = self.request.user.tenant_name
            networks = api.neutron.network_list(request, tenant_name=tenant_name, shared=False)
            for n in networks:
                n.set_id_as_name_if_empty()
            network_list = [(network.id, network.name) for network in networks]
        except:
            network_list = []
            exceptions.handle(request,
                              _('Unable to retrieve networks.'))
        return network_list

class CreateVPNInfo(workflows.Step):
    action_class = CreateVPNInfoAction
    # contributes = ("vpntype", "private_net_name", "net_name", "private", "private_network_id")
    contributes = ("vpntype", "private_network_id", "net_name")


class CreateSiteInfoAction(workflows.Action):
    with_site = forms.BooleanField(label=_("Add a remote Openstack cloud site to this VPN?"), initial=False, required=False)
    CHOICES = (('Data_Center_San_Jose_B', 'Enterprise Data Center in San Jose B'), ('Data_Center_Jorvas', 'Enterprise Data Center in Jorvas'))

    #sitechoice = forms.ChoiceField(required=False, label='Existent Enterprise Site:', choices=CHOICES)
 
    site_name = forms.CharField(max_length=255,
                                  label=_("Name of remote Openstack Site running VPN Agent:"),
                                  help_text=_("Remote Site Name. This field is "
                                           "optional."),
                                  required=False)
    keystone = fields.IPField(label=_("Remote Keystone IP Address:"),
                          required=False,
                          initial="10.126.71.249",
                          help_text=_("Remote Keystone Network address in IPv4 or IPv6 address format "
                                      "(e.g. 192.168.0.0)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=False)
    
    user = forms.CharField(max_length=255,
                                  label=_("Username in Remote site"),
                                  help_text=_("Tenant's user LOGIN in Enterprise site. In case you do not want to provide a 24hours expiration token from your Enterprise Keystone "
                                        "each time you connect your VPN. This field is "
                                           "optional."),
                                  required=False)
    password = forms.CharField(label=_("Password:"),
                                  help_text=_("User PASSWORD in Remote site used to generate the token. This field is "
                                           "optional."), widget=forms.PasswordInput(render_value=False), required=False)
    tenant = forms.CharField(label=_("and Tenant Name:"),
                                  help_text=_("Tenant's NAME in Enterprise site. This field is "
                                           "optional."), required=False)


    class Meta:
        name = ("Local and Remote Sites")
        help_text = _('You can add a Remote Openstack Provider Cloud Site as well as your Enterprise Site associated with the new '
                      'VPN. You need to provide your credentials in remote site so that we generate a token on your behalf. ')
    def _check_site_data(self, cleaned_data, is_create=True):
        rke = cleaned_data.get('keystone')
        ws = cleaned_data.get('with_site')
	sn= cleaned_data.get('site_name')
	lg= cleaned_data.get('user')
	tn= cleaned_data.get('tenant')
	pw= cleaned_data.get('password')

        if not rke:
            msg = _('Specify "Enterprise Keystone IP Address" or '
                    'clear "Add your Enterprise Site to this VPN" checkbox.')
            raise forms.ValidationError(msg)
        if rke:
            site = netaddr.IPNetwork(rke)
        #    if site.version != ip_version:
        #        msg = _('Keystone IP Address and IP version are inconsistent.')
        #        raise forms.ValidationError(msg)
	if sn and not rke:
	    msg = _('Make sure you added a keystone endpoint for you newly added site')
            raise forms.ValidationError(msg)
	#if sn and rke and not tk and not lg:
        #    msg = _('Make sure you added a login if you do not provide a token for  your new site')
        #    raise forms.ValidationError(msg)
	if lg and not tn:
	    msg = _('Make sure you added a tenant for the login your provided')
            raise forms.ValidationError(msg)
        if lg and not pw:
            msg = _('Make sure you added a password for the login your provided')
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
    contributes = ("with_site",  "site_name", "keystone", "user", "password", "tenant")

class CreateVPNDetailAction(workflows.Action):
   
    id = forms.IntegerField(max_value=2147483647,min_value=0,
				  label=_("ID"),
				  help_text=_("ID for VPN Table"),
				  required=True) 
    vpn_name = forms.CharField(max_length=255,
                                  label=_("Name your IP-Sec Connectivity"),
                                  help_text=_("IP-Sec Connectivity Name. This field is "
                                           "optional."),
                                  required=False)
    
    tenant_name = forms.CharField(max_length=255, required=True,
                                  label='Tenant Name', help_text=_("Enter a Tenant Name - it takes a string"))

    branch_name = forms.CharField(max_length=255, required=True,
                                  label='Branch Name', help_text=_("Enter a Branch Name - it takes a string"))

    key_name = forms.CharField(max_length=255,
				label=_("Enter a Secret/Password for the ip-sec connection."),
				help_text=_("SecretKey. This field is required and will be used"
                                            " as the PSK for establishing a strong-swan ipsec connection."),
				required=True)


    class Meta:
        name = ("Local and Remote Gateways")
        help_text = _('You can specify the Local (Provider) and Remote (Enterprise) Gateways in Local and Remote Sites resp. to add to this VPN.')

    def __init__(self, request, context, *args, **kwargs):
        self._init_images_cache()
        self.request = request
        self.context = context
        super(CreateVPNDetailAction, self).__init__(
            request, context, *args, **kwargs)

    def clean(self):
        cleaned_data = super(CreateVPNDetailAction, self).clean()
        return cleaned_data
  
    def _init_images_cache(self):
        if not hasattr(self, '_images_cache'):
            self._images_cache = {}
    
    @memoized.memoized_method
    def _get_keypair(self, keypair):
        try:
            # We want to retrieve details for a given keypair,
            # however keypair_list uses a memoized decorator
            # so it is used instead of keypair_get to reduce the number
            # of API calls.
            keypairs = instance_utils.keypair_list(self.request)
            keypair = [x for x in keypairs if x.id == keypair][0]
        except IndexError:
            keypair = None
        return keypair
   
    @memoized.memoized_method
    def _get_flavor(self, flavor_id):
        try:
            # We want to retrieve details for a given flavor,
            # however flavor_list uses a memoized decorator
            # so it is used instead of flavor_get to reduce the number
            # of API calls.
            flavors = instance_utils.flavor_list(self.request)
            flavor = [x for x in flavors if x.id == flavor_id][0]
        except IndexError:
            flavor = None
        return flavor

    @memoized.memoized_method
    def _get_image(self, image_id):
        try:
            # We want to retrieve details for a given image,
            # however get_available_images uses a cache of image list,
            # so it is used instead of image_get to reduce the number
            # of API calls.
            images = image_utils.get_available_images(
                self.request,
                self.context.get('project_id'),
                self._images_cache)
            image = [x for x in images if x.id == image_id][0]
        except IndexError:
            image = None
        return image

    def populate_keypair_choices(self, request, context):
        keypairs = instance_utils.keypair_field_data(request, False)
        if len(keypairs) == 2:
            self.fields['keypair'].initial = keypairs[1][0]
        return keypairs

    def populate_groups_choices(self, request, context):
        try:
            groups = api.network.security_group_list(request)
            security_group_list = [(sg.name, sg.name) for sg in groups]
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve list of security groups'))
            security_group_list = []
        return security_group_list
 
    def populate_flavor_choices(self, request, context):
        return instance_utils.flavor_field_data(request, False)
     
    def populate_image_id_choices(self, request, context):
        choices = []
        images = image_utils.get_available_images(request,
                                                  context.get('project_id'),
                                                  self._images_cache)
        for image in images:
            image.bytes = image.virtual_size or image.size
            image.volume_size = max(
                image.min_disk, functions.bytes_to_gigabytes(image.bytes))
            choices.append((image.id, image))
            if context.get('image_id') == image.id and \
                    'volume_size' not in context:
                context['volume_size'] = image.volume_size
        if choices:
            choices.sort(key=lambda c: c[1].name)
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        return choices
    
    def get_help_text(self, extra_context=None):
        extra = {} if extra_context is None else dict(extra_context)
        try:
            extra['usages'] = api.nova.tenant_absolute_limits(self.request)
            extra['usages_json'] = json.dumps(extra['usages'])
            flavors = json.dumps([f._info for f in
                                  instance_utils.flavor_list(self.request)])
            extra['flavors'] = flavors
            images = image_utils.get_available_images(
                self.request, images_cache=self._images_cache)
            if images is not None:
                attrs = [{'id': i.id,
                          'min_disk': getattr(i, 'min_disk', 0),
                          'min_ram': getattr(i, 'min_ram', 0),
                          'size': functions.bytes_to_gigabytes(i.size)}
                         for i in images]
                extra['images'] = json.dumps(attrs)

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))
        return super(CreateVPNDetailAction, self).get_help_text(extra)


class CreateVPNDetail(workflows.Step):
    action_class = CreateVPNDetailAction
    #contributes = ("with_gw", "rgwchoice", "name", "gw_endpoint", "tenant_name", "branch_name", 
    #		"keypair", "image_id", "flavor", "volume_size")
    contributes = ("id", "vpn_name", "tenant_name", "branch_name", 
    		"key_name")
    
    def contribute(self, data, context):

        if data:
	    context["id"] = data.get("id", "")
            context["vpn_name"] = data.get("vpn_name", "")
            context["tenant_name"] = data.get("tenant_name", "")
            context["branch_name"] = data.get("branch_name", "")
            context["key_name"] = data.get("key_name", "")
        return context

class SetCloudNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(label=_("Networks"),
                                        widget=forms.CheckboxSelectMultiple(),
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Launch instance with"
                                                    " these networks"))
    if api.neutron.is_port_profiles_supported():
        widget = None
    else:
        widget = forms.HiddenInput()
    profile = forms.ChoiceField(label=_("Policy Profiles"),
                                required=False,
                                widget=widget,
                                help_text=_("Launch instance with "
                                            "this policy profile"))

    def __init__(self, request, *args, **kwargs):
        super(SetCloudNetworkAction, self).__init__(request, *args, **kwargs)
        network_list = self.fields["network"].choices
        if len(network_list) == 1:
            self.fields['network'].initial = [network_list[0][0]]
        if api.neutron.is_port_profiles_supported():
            self.fields['profile'].choices = (
                self.get_policy_profile_choices(request))

    class Meta(object):
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def populate_network_choices(self, request, context):
        return instance_utils.network_field_data(request)

    def get_policy_profile_choices(self, request):
        profile_choices = [('', _("Select a profile"))]
        for profile in self._get_profiles(request, 'policy'):
            profile_choices.append((profile.id, profile.name))
        return profile_choices

    def _get_profiles(self, request, type_p):
        profiles = []
        try:
            profiles = api.neutron.profile_list(request, type_p)
        except Exception:
            msg = _('Network Profiles could not be retrieved.')
            exceptions.handle(request, msg)
        return profiles

class SetCloudNetwork(workflows.Step):
    action_class = SetCloudNetworkAction
    # Disabling the template drag/drop only in the case port profiles
    # are used till the issue with the drag/drop affecting the
    # profile_id detection is fixed.
    if api.neutron.is_port_profiles_supported():
        contributes = ("network_id", "profile_id",)
    else:
        template_name = "project/instances/_update_networks.html"
        contributes = ("network_id",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            if networks:
                context['network_id'] = networks

            if api.neutron.is_port_profiles_supported():
                context['profile_id'] = data.get('profile', None)
        return context

'''class UpdateInstanceSecurityGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateInstanceSecurityGroupsAction, self).__init__(request,
                                                                 *args,
                                                                 **kwargs)
        err_msg = _('Unable to retrieve security group list. '
                    'Please try again later.')
        context = args[0]
        instance_id = context.get('instance_id', '')

        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = 'member'

        # Get list of available security groups
        all_groups = []
        try:
            all_groups = api.network.security_group_list(request)
	except Exception:
            exceptions.handle(request, err_msg)
        groups_list = [(group.id, group.name) for group in all_groups]

        instance_groups = []
        try:
            instance_groups = api.network.server_security_groups(request,
                                                                 instance_id)
        except Exception:
            exceptions.handle(request, err_msg)
        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)
        self.fields[field_name].choices = groups_list
        self.fields[field_name].initial = [group.id
                                           for group in instance_groups]

    def handle(self, request, data):
        instance_id = data['instance_id']
        wanted_groups = map(filters.get_int_or_uuid, data['wanted_groups'])
        try:
            api.network.server_update_security_groups(request, instance_id,
                                                      wanted_groups)
        except Exception as e:
            exceptions.handle(request, str(e))
            return False
        return True

    class Meta(object):
	name = _("Security Groups")
        slug = INSTANCE_SEC_GROUP_SLUG


class UpdateInstanceSecurityGroups(workflows.UpdateMembersStep):
    action_class = UpdateInstanceSecurityGroupsAction
    help_text = _("Add and remove security groups to this project "
                  "from the list of available security groups.")
    available_list_title = _("All Security Groups")
    members_list_title = _("Instance Security Groups")
    no_available_text = _("No security groups found.")
    no_members_text = _("No security groups enabled.")
    show_roles = False
    depends_on = ("instance_id",)
    contributes = ("wanted_groups",)

    def contribute(self, data, context):
        request = self.workflow.request
        if data:
            field_name = self.get_member_field_name('member')
            context["wanted_groups"] = request.POST.getlist(field_name)
        return context'''

class CreateCloudSubnetAction(workflows.Action):
    with_subnet = forms.BooleanField(label=_("Create Cloud Subnet"),
                                     widget=forms.CheckboxInput(attrs={
                                         'class': 'switchable',
                                         'data-slug': 'with_subnet',
                                         'data-hide-tab': 'create_network__'
                                                          'createsubnetdetail'
                                                          'action',
                                         'data-hide-on-checked': 'false'
                                     }),
                                     initial=True,
                                     required=False)
    cloud_subnet_name = forms.CharField(max_length=255,
                                  widget=forms.TextInput(attrs={
                                      'class': 'switched',
                                      'data-switch-on': 'with_subnet',
                                  }),
                                  label=_("Cloud Subnet Name"),
                                  required=False)
    '''gateway_subnet = forms.IPField(label=_("Network Address"),
                         required=False,
                         initial="",
                         widget=forms.TextInput(attrs={
                             'class': 'switched',
                             'data-switch-on': 'with_subnet',
                             'data-is-required': 'true'
                         }),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24, 2001:DB8::/48)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True)'''

    gateway_subnet = forms.CharField(label=_("Network Address"),
                            max_length=255,
                            required=False,
                            initial="",
                            widget=forms.TextInput(attrs={
                                'class': 'switched',
                                'data-switch-on': 'with_subnet',
                                'data-is-required': 'true'
                            }),
                            help_text=_("Network address in CIDR format "
                                        "(e.g. 192.168.0.0/24, 2001:DB8::/48)"))
    ip_version = forms.ChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
                                   widget=forms.Select(attrs={
                                       'class': 'switchable switched',
                                       'data-slug': 'ipversion',
                                       'data-switch-on': 'with_subnet'
                                   }),
                                   label=_("IP Version"))
    gateway_ip = forms.CharField(
        max_length=255,
        label=_("Cloud Gateway IP"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'with_subnet gateway_ip'
        }),
        required=False,
	initial="",
        help_text=_("IP address of Cloud Gateway (e.g. 192.168.0.254) "
                    "The default value is the first IP of the "
                    "network address "
                    "(e.g. 192.168.0.1 for 192.168.0.0/24, "
                    "2001:DB8::1 for 2001:DB8::/48). "
                    "If you use the default, leave blank. "
                    "If you do not want to use a gateway, "
                    "check 'Disable Gateway' below."))
    
    '''gateway_ip = forms.IPField(
        label=_("Cloud Gateway IP"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'with_subnet gateway_ip'
        }),
        required=False,
	initial="",
        help_text=_("IP address of Cloud Gateway (e.g. 192.168.0.254) "
                    "The default value is the first IP of the "
                    "network address "
                    "(e.g. 192.168.0.1 for 192.168.0.0/24, "
                    "2001:DB8::1 for 2001:DB8::/48). "
                    "If you use the default, leave blank. "
                    "If you do not want to use a gateway, "
                    "check 'Disable Gateway' below."),
        version=forms.IPv4 | forms.IPv6,
        mask=False)'''
    no_gateway = forms.BooleanField(label=_("Disable Gateway"),
                                    widget=forms.CheckboxInput(attrs={
                                        'class': 'switched switchable',
                                        'data-slug': 'gateway_ip',
                                        'data-switch-on': 'with_subnet',
                                        'data-hide-on-checked': 'true'
                                    }),
                                    initial=False,
                                    required=False)
    msg = _('Specify "Network Address" or '
            'clear "Create Cloud Subnet" checkbox.')

    class Meta(object):
        name = _("Cloud Subnet")
        help_text = _('Create a subnet associated with the cloud network, '
                      'in which case "Network Address" must be specified. '
                      'If you wish to create a network without a subnet, '
                      'uncheck the "Create Cloud Subnet" checkbox.')

    def __init__(self, request, context, *args, **kwargs):
        super(CreateCloudSubnetAction, self).__init__(request, context, *args,
                                                     **kwargs)
        if not getattr(settings, 'OPENSTACK_NEUTRON_NETWORK',
                       {}).get('enable_ipv6', True):
            self.fields['ip_version'].widget = forms.HiddenInput()
            self.fields['ip_version'].initial = 4

    def _check_subnet_data(self, cleaned_data, is_create=True):
        gateway_subnet = cleaned_data.get('gateway_subnet')
        ip_version = int(cleaned_data.get('ip_version'))
        gateway_ip = cleaned_data.get('gateway_ip')
        no_gateway = cleaned_data.get('no_gateway')
	if gateway_ip == "flotilla-gateway.t-labs.us":
	    gateway_ip = "12.37.166.247"
        if not gateway_subnet:
            raise forms.ValidationError(self.msg)
	if gateway_subnet:
            subnet = netaddr.IPNetwork(gateway_subnet)
            if subnet.version != ip_version:
                msg = _('Network Address and IP version are inconsistent.')
                raise forms.ValidationError(msg)
            if (ip_version == 4 and subnet.prefixlen == 32) or \
                    (ip_version == 6 and subnet.prefixlen == 128):
                msg = _("The subnet in the Network Address is "
                        "too small (/%s).") % subnet.prefixlen
                raise forms.ValidationError(msg)
	if not no_gateway and gateway_ip:
	    if netaddr.IPAddress(gateway_ip).version is not ip_version:
                msg = _('Gateway IP and IP version are inconsistent.')
                raise forms.ValidationError(msg)
        if not is_create and not no_gateway and not gateway_ip:
            msg = _('Specify IP address of gateway or '
                    'check "Disable Gateway".')
            raise forms.ValidationError(msg)

    def clean(self):
        cleaned_data = super(CreateCloudSubnetAction, self).clean()
        with_subnet = cleaned_data.get('with_subnet')
        if not with_subnet:
            return cleaned_data
        self._check_subnet_data(cleaned_data)
        return cleaned_data


class CreateCloudSubnet(workflows.Step):
    action_class = CreateCloudSubnetAction
    contributes = ("with_subnet", "cloud_subnet_name", "gateway_subnet",
                   "ip_version", "gateway_ip", "no_gateway")

class CreateBranchSubnetAction(workflows.Action):
    with_subnet = forms.BooleanField(label=_("Create Branch Subnet"),
                                     widget=forms.CheckboxInput(attrs={
                                         'class': 'switchable',
                                         'data-slug': 'with_subnet',
                                         'data-hide-tab': 'create_network__'
                                                          'createsubnetdetail'
                                                          'action',
                                         'data-hide-on-checked': 'false'
                                     }),
                                     initial=True,
                                     required=False)
    branch_subnet_name = forms.CharField(max_length=255,
            widget=forms.TextInput(attrs={
                                      'class': 'switched',
                                      'data-switch-on': 'with_subnet',
                                  }),
                                  label=_("Branch Subnet Name"),
                                  required=False)
    '''branch_subnet = forms.IPField(label=_("Network Address"),
                         required=False,
                         initial="",
                         widget=forms.TextInput(attrs={
                             'class': 'switched',
                             'data-switch-on': 'with_subnet',
                             'data-is-required': 'true'
                         }),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24, 2001:DB8::/48)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True)'''
    branch_subnet = forms.CharField(max_length=255,
                         label=_("Network Address"),
                         required=False,
                         initial="",
                         widget=forms.TextInput(attrs={
                             'class': 'switched',
                             'data-switch-on': 'with_subnet',
                             'data-is-required': 'true'
                         }),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24, 2001:DB8::/48)"))
    ip_version = forms.ChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
                                   widget=forms.Select(attrs={
                                       'class': 'switchable switched',
                                       'data-slug': 'ipversion',
                                       'data-switch-on': 'with_subnet'
                                   }),
                                   label=_("IP Version"))
    branch_ip = forms.CharField(max_length=255,
        label=_("Branch Gateway IP"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'with_subnet branch_ip'
        }),
        required=False,
	initial="",
        help_text=_("IP address of Branch Gateway (e.g. 192.168.0.254) "
                    "The default value is the first IP of the "
                    "network address "
                    "(e.g. 192.168.0.1 for 192.168.0.0/24, "
                    "2001:DB8::1 for 2001:DB8::/48). "
                    "If you use the default, leave blank. "
                    "If you do not want to use a gateway, "
                    "check 'Disable Gateway' below."))
    no_gateway = forms.BooleanField(label=_("Disable Gateway"),
                                    widget=forms.CheckboxInput(attrs={
                                        'class': 'switched switchable',
                                        'data-slug': 'gateway_ip',
                                        'data-switch-on': 'with_subnet',
                                        'data-hide-on-checked': 'true'
                                    }),
                                    initial=False,
                                    required=False)
    msg = _('Specify "Network Address" or '
            'clear "Create Branch Subnet" checkbox.')

    class Meta(object):
        name = _("Branch Subnet")
        help_text = _('Create a subnet associated with the branch network, '
                      'in which case "Network Address" must be specified. '
                      'If you wish to create a network without a subnet, '
                      'uncheck the "Create Branch Subnet" checkbox.')

    def __init__(self, request, context, *args, **kwargs):
        super(CreateBranchSubnetAction, self).__init__(request, context, *args,
                                                     **kwargs)
        if not getattr(settings, 'OPENSTACK_NEUTRON_NETWORK',
                       {}).get('enable_ipv6', True):
            self.fields['ip_version'].widget = forms.HiddenInput()
            self.fields['ip_version'].initial = 4

    def _check_subnet_data(self, cleaned_data, is_create=True):
        branch_subnet = cleaned_data.get('branch_subnet')
        ip_version = int(cleaned_data.get('ip_version'))
        branch_ip = cleaned_data.get('branch_ip')
        no_gateway = cleaned_data.get('no_gateway')
	if branch_ip == "aquarium.t-labs.us":
	    branch_ip = "12.37.166.242"
        if not branch_subnet:
            raise forms.ValidationError(self.msg)
        if branch_subnet:
            subnet = netaddr.IPNetwork(branch_subnet)
            if subnet.version != ip_version:
                msg = _('Network Address and IP version are inconsistent.')
                raise forms.ValidationError(msg)
            if (ip_version == 4 and subnet.prefixlen == 32) or \
                    (ip_version == 6 and subnet.prefixlen == 128):
                msg = _("The subnet in the Network Address is "
                        "too small (/%s).") % subnet.prefixlen
                raise forms.ValidationError(msg)
            
        if not no_gateway and branch_ip:
            if netaddr.IPAddress(branch_ip).version is not ip_version:
                msg = _('Gateway IP and IP version are inconsistent.')
                raise forms.ValidationError(msg)
        if not is_create and not no_gateway and not branch_ip:
            msg = _('Specify IP address of gateway or '
                    'check "Disable Gateway".')
            raise forms.ValidationError(msg)

    def clean(self):
        cleaned_data = super(CreateBranchSubnetAction, self).clean()
        with_subnet = cleaned_data.get('with_subnet')
        if not with_subnet:
            return cleaned_data
        self._check_subnet_data(cleaned_data)
        return cleaned_data


class CreateBranchSubnet(workflows.Step):
    action_class = CreateBranchSubnetAction
    contributes = ("with_subnet", "branch_subnet_name", "branch_subnet",
                   "ip_version", "branch_ip", "no_gateway")



class CreateVPN(workflows.Workflow):
    #slug = "create_vpn"
    slug = "ipsec"
    name = _("Create VPN")
    finalize_button_name = _("Create VPN")
    success_message = _('Created VPN Connectivity "%s".')
    failure_message = _('Unable to create vpn"%s".')
    default_steps = (CreateVPNDetail,
		     CreateCloudSubnet,
		     CreateBranchSubnet)
		     #SetCloudNetwork,
                     #SetBranchNetwork)
                     #UpdateInstanceSecurityGroups)
    success_url= 'horizon:project:ipsec:index'

    def clean(self, sentence):
	return sentence.replace(" ", "")
	
    def get_success_url(self):
        return reverse("horizon:project:ipsec:index")

    def get_failure_url(self):
        return reverse("horizon:project:ipsec:index")

    def format_status_message(self, message):
        name = self.context.get('net_name') or self.context.get('net_id', '')
        return message % name

    '''def _create_gw(self, request, data):
        try:
	    sites = self._add_sites(self, request, data, no_redirect=True)
            #gw=api.elasticnet.elasticnet_network_create(request, self.clean(data['net_name']), data['vpntype'])
            messages.success(request, _("Gateway created successfully."))
	    return sites
        except:
            exceptions.handle(request, _('Unable to create gateway.'))
        return shortcuts.redirect(self.success_url)'''

    def _add_sites(self, request, data, vpn=None, tenant_name=None,
                       no_redirect=False):
        if vpn:
            vpn_id = vpn['vpn']['id']
	    vpn_name = self.clean(data['net_name'])
        else:
            #vpn_id = self.context.get('vpn_id')
	    #vpn_name = self.context.get('vpn_name')
	    vpn_id = random.randint(1,1000)
	    vpn_name = "T-VPN"
        try:
	    
	    o = urlparse.urlparse(url_for(request, "compute"))
	    hostname= str(o.hostname)
	    #if str(request.user.username).startswith("acme"):
	    #	hostname="10.199.199.30" 
            lsite=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.Provider_AZ1', hostname, '', str(request.user.username), str(request.user.token.id), str(request.user.tenant_name))
            messages.success(request, _("Local Provider Site %s added successfully.")% vpn_name+'.Provider_AZ1')

	    data['token']=''
            if data['site_name']:
		rsite=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.'+ self.clean(data['site_name']),  data['keystone'], data['token'], data['user'], data['password'], data['tenant'])
		messages.success(request, _("Enterprise Site %s added successfully.")% vpn_name+'.'+ self.clean(data['site_name']))
            #else:
            #    rsite=api.elasticnet.elasticnet_add_site(request, vpn_id, vpn_name+'.'+data['sitechoice'],  data['keystone'], data['token'], data['user'], data['password'], data['tenant'])
            #    messages.success(request, _("Enterprise Site %s added successfully.")% vpn_name+'.'+data['sitechoice'])
	    return rsite
        except Exception as e:
            if no_redirect:
                redirect = None
            else:
                redirect = self.get_failure_url()
            exceptions.handle(request,
                              "Failed to add site because %s"%e,
                              redirect=redirect)
            return False

    def _add_vpn(self, request, data, vpn=None, tenant_name=None,
                       no_redirect=False):
	#vpn_id = random.randint(1,1000)
	if vpn:
            #vpn_id = vpn['vpn']['id']
            vpn_name = self.clean(data['net_name'])
        else:
            #vpn_id = self.context.get('vpn_id')
            #vpn_name = self.context.get('vpn_name')
	    #vpn_id = random.randint(1,1000)
            vpn_name = "T-VPN"
	rgw=None
	try:
            #if data['sitechoice'] in ['new', '']:
            #    print "create a new gw -- not implemented yet"
            #else:
		# auto discover is not implemented yet, so choose one first gw in provider site
                

	    '''lgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.Provider_AZ1', vpn_name+'.Provider_AZ1.GW1')
		if data['site_name']:
		  if data['gw_name']:
                    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+self.clean(data['site_name']), vpn_name+'.'+ self.clean(data['site_name'])+'.'+ self.clean(data['gw_name']))
		  else:
		    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+self.clean(data['site_name']), vpn_name+'.'+ self.clean(data['site_name'])+'.'+data['rgwchoice'])
	    '''
	    url = 'http://127.0.0.1:7007/connect_ipsec'
            LOG.debug("DATA in add_ipsec: {0}".format(data))
	    vpn_name = data['vpn_name']
	    LOG.debug("vpn_name:".format(vpn_name))
	    #gw_ip = data['gw_endpoint']
            id = data['id']
            LOG.debug("vpn_id: {0}".format(id))
	    tenant_name = data['tenant_name']
	    LOG.debug("tenant_name: {0}".format(tenant_name))
	    branch_name = data['branch_name']
	    LOG.debug("branch_name: {0}".format(branch_name))
	    secret = data['key_name']
	    LOG.debug("secret: {0}".format(secret))
            gateway_ip = data['gateway_ip']
            branch_ip = data['branch_ip']
	    gateway_name = data['cloud_subnet_name']
	    LOG.debug("cloud_gateway_name: {0}".format(gateway_name))
            gateway_subnet = data['gateway_subnet']
            LOG.debug("gateway_subnet: {0}".format(gateway_subnet))
            branch_subnet = data['branch_subnet']
            LOG.debug("branch_subnet: {0}".format(branch_subnet))

	    payload = { "id": id, "vpn_name" : vpn_name, "tenant_name" : tenant_name, "branch_name" : branch_name, 
                    "secret" : secret, "gateway_ip" : gateway_ip, "gateway_name": gateway_name,
                "branch_ip" : branch_ip, "gateway_subnet" : gateway_subnet,
                "branch_subnet" : branch_subnet}
	    headers = {'content-type': 'application/json'}
	    req = requests.post(url, data=json.dumps(payload), headers = headers)

		

	    #else:
	    #  if data['gw_name']:
            #    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+data['sitechoice'], vpn_name+'.'+data['sitechoice']+'.'+  self.clean(data['gw_name']))
	    #  else:
	    #    rgw=api.elasticnet.elasticnet_add_gw(request, vpn_id, vpn_name+'.'+data['sitechoice'], vpn_name+'.'+data['sitechoice']+'.'+data['rgwchoice'])
            messages.success(request, _("Gateways added successfully."))
	    #return rgw
	    return True
        except Exception as e:
            if no_redirect:
                redirect = None
            else:
                redirect = self.get_failure_url()
            exceptions.handle(request,
                              "Failed to add gw %s because %s"%(data['rgwchoice'], e),
                              redirect=redirect)
            return False


    '''def _delete_vpn(self, request, vpn):
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
            exceptions.handle(request, msg, redirect=redirect)'''

    def handle(self, request, data):
	LOG.debug("Request: {0}".format(request))
	LOG.debug("DATA in handle: {0}".format(data))
	#gw_name = data['gw_name']
        '''gw = self._create_gw(request, data)
        if not gw:
            return False
        # If we do not need to add a site, return here.
        if not data['with_site']:
            return True'''
        #sites = self._add_sites(request, data, no_redirect=True)
        #if sites:
	#    if not data['with_gw']:
        #        return True
	net = self._add_vpn(request, data, no_redirect=True)
        if net:
            return True
        else:
            '''self._delete_vpn(request, vpn)'''
        return True

