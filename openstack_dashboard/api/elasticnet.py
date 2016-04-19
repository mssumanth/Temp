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

from restful_lib import Connection

import json
#from __future__ import absolute_import

import logging
import random
#from quantumclient.v2_0 import client as quantum_client
from django.utils.datastructures import SortedDict

from horizon.conf import HORIZON_CONFIG

from openstack_dashboard.api.base import APIDictWrapper, url_for
#from openstack_dashboard.api import network
#from openstack_dashboard.api import nova

from horizon import exceptions
from openstack_dashboard.api.elasticnetclient import client as elasticnet_client
#from openstack_dashboard.api.elasticnetclient import cli_lib
#
import functools
import logging
import urlparse
import requests
from django.utils.decorators import available_attrs


url="image not generated"
LOG = logging.getLogger(__name__)


class VPN(APIDictWrapper):
    _attrs = ['id', 'name', 'nettype', 'state' ,'bw']

class Site(APIDictWrapper):
    _attrs = ['id', 'name', 'keystone', 'token', 'user', 'password', 'tenant', 'ip', 'certificate', 'state']

class GW(APIDictWrapper):
    _attrs = ['id', 'name', 'site', 'state']

class Link(APIDictWrapper):
    _attrs = ['id', 'gwid1', 'gwid2', 'bw', 'state', 'eir', 'cbs', 'pbs']

class Port(APIDictWrapper):
    _attrs = ['id', 'attachment_server', 'attachment_id', 'state', 'op-status']


class Vif(APIDictWrapper):
    _attrs = ['id']

class CloudGw:
    def __init__(self, name, image_id, keypair, tenant_name, branch_name, id=random.randint(1,1000000)):
        self.id = random.randint(1,1000000)
        self.name = name
        self.image_id = image_id
        self.keypair = keypair
        self.tenant_name = tenant_name
        self.branch_name = branch_name
        self.ip_group = "public"
        self.addresses = {"public":"172.0.0.0"}
        self.instance_id = "4040"
        self.subnets = "10.0.0.0/24"

class VPN:
    def __init__(self, name, tenant_name, branch_name, cloud_gw_ip, cloud_subnet, branch_gw_ip, branch_subnet, id=random.randint(1,1000000)):
        self.id = id
	#= random.randint(1,1000000)
        self.vpn_name = name
        self.tenant_name = tenant_name
        self.branch_name = branch_name
        self.gateway_ip = cloud_gw_ip#"10.0.1.123"
        self.branch_ip = branch_gw_ip#"10.0.2.123"
        self.gateway_subnet = cloud_subnet#"10.0.1.0/24"
        self.branch_subnet = branch_subnet#"10.0.2.0/24"
        self.ip_group = "public"
        self.addresses = {"public":"172.0.0.0"}
        self.subnets = "10.0.0.0/24"
	
    def getInfo(self):
        return {'id':self.id, 'vpn_name': self.vpn_name, 'tenant_name':self.tenant_name, 'branch_name':self.branch_name, 'gateway_ip':self.gateway_ip, 'branch_ip':self.branch_ip, 
        'gateway_subnet':self.gateway_subnet, 'branch_subnet':self.branch_subnet}    


def getGatewayList(self):
    try: 
        headers = {'content-type': 'application/json'}
        url = 'http://127.0.0.1:7007/gateway_list'
        responses = requests.get(url, verify=False, headers = headers)
        print "Responses in getGatewayList: ",responses.json()
        rsp = []
        for response in responses.json():
            print "response:", response
            rsp.append(CloudGw(response['gateway_name'], 
                    response['image_id'], response['keypair'], 
                    response['tenant_name'], response['branch_name'], response['id']))
        print "RSP is: ",rsp
        return rsp
    except:
        #exceptions.handle(self.request, _('Unable to get providers'))
        print "Sumanth caught exception"
        entry = {#'id' : "4",
                'name' : "dt100",
                'tenant_name' : "2",
                'branch_name' : "2000",
                'keypair' : "cloudgw",
                'instance_id' : "700",
                'image_id' : "cirros",
                'subnets' : "10.0.0.0/24",
                'cloud_gw_ip' : "10.0.1.123/24",
                'branch_gw_ip' : "10.0.2.123/24",
                'cloud_subnet' : "10.0.1.0/24",
                'branch_subnet' : "10.0.2.0/24"}
        rsp=[]
        rsp.append(entry)
        return rsp

def getVPNList(self):
    try: 
        headers = {'content-type': 'application/json'}
        url = 'http://127.0.0.1:7007/vpn_list'
        responses = requests.get(url, verify=False, headers = headers)
        print "Responses in getVPNList: ",responses.json()
        rsp = []
        for response in responses.json():
            print "response in getVPNList:", response
            print "vpn_name:", response['vpn_name']
            rsp.append(VPN(response['vpn_name'], 
                    response['tenant_name'], response['branch_name'],
                    response['gateway_ip'], response['gateway_subnet'],
                    response['branch_ip'], response['branch_subnet'], response['id']))
        return rsp
    except:
        #exceptions.handle(self.request, _('Unable to get providers'))
        print "caught exception"
        entry = { 
                'name' : "dt100",
                'tenant_name' : "2",
                'branch_name' : "2000",
                'gateway_ip' : "10.0.1.121",
                'cloud_subnet' : "10.0.1.0/24",
                'branch_ip' : "10.0.2.121",
                'branch_subnet' : "10.0.2.0/24" }
        rsp=[]
        rsp.append(entry)
        return rsp

def elasticnetclient(request):
    #LOG.debug('elasticnetclient connection created using token "%s" and url "%s"'
    #          % (request.user.token.id, url_for(request, "vpn")))
    #LOG.debug('user_id=%(user)s, tenant_name=%(tenant)s' %
    #          {'user': request.user.id, 'tenant': request.user.tenant_name})
    
    print "ELASTICNET::elasticnetclient:Request- ",request
    o = urlparse.urlparse(url_for(request, "vpns"))
    if request.user.username.startswith("adidas"):
	o = urlparse.urlparse(url_for(request, "ipsecvpn"))
    print (' *********** elasticnet client connection created for host "%s:%d"' %
              (o.hostname, o.port))
    return elasticnet_client.ENClient(o.hostname,
                                 o.port,
                                 #tenant=request.user.tenant_name,
				 tenant="adidas",
                                 auth_token=request.user.token.id)
    
    '''hostname = '127.0.0.1'
    port = '7007'
    url = 'horizon:project:vpns:creategw'
    return elasticnet_client.ENClient(hostname,
                                 port,
                                 #tenant=request.user.tenant_name,
				 tenant="adidas",
                                 auth_token=request.user.token.id)'''


def elasticnet_network_list(request):
    e_networks = elasticnetclient(request).list_vpns()
    print "e_networks = %s"%e_networks
    networks = []
    for network in e_networks['vpns']:
        # Get detail for this network
        det = elasticnetclient(request).show_vpn_details(network['id'])
	print "det details %s"%det
        # Get ports for this network
        #ports = elasticnetclient(request).list_ports(network['id'])
        sites= elasticnetclient(request).list_sites(network['id'])
        gws= elasticnetclient(request).list_gateways(network['id'])
        links= elasticnetclient(request).list_links(network['id'])
	det['vpn']['site_count'] = len(sites['sites'])
	det['vpn']['gw_count'] = len(gws['gateways'])
	det['vpn']['link_count'] = len(links['links'])
	abw=0
	for l in links['links']:
	   print "++++++++++ l=%s="%l
	   if l['state']=='CONNECTED':
	     abw=abw+int(l['bw'])
	det['vpn']['bw']=abw
	det['vpn']['branchvm']=getBranchGwVM(request, network['id'])
	det['vpn']['status']='DISCONNECTED'
	if abw>0:
	   det['vpn']['status']='CONNECTED'
        networks.append(VPN(det['vpn']))
    return networks

def getBranchGwVM(request, elasticnet_id):
    
    return "http://129.192.170.90/branchvpn2ericsson.ova"

def elasticnet_network_get(request, elasticnet_id):
        # Get detail for this network
        det = elasticnetclient(request).show_vpn_details(elasticnet_id)
        print "det details %s"%det
        # Get ports for this network
        #ports = elasticnetclient(request).list_ports(network['id'])
        sites= elasticnetclient(request).list_sites(elasticnet_id)
        gws= elasticnetclient(request).list_gateways(elasticnet_id)
        links= elasticnetclient(request).list_links(elasticnet_id)
        det['vpn']['site_count'] = len(sites['sites'])
        det['vpn']['gw_count'] = len(gws['gateways'])
        det['vpn']['link_count'] = len(links['links'])
        abw=0
        for l in links['links']:
           print "++++++++++ l=%s="%l
           if l['state']!='DISCONNECTED' or l['state']!='Disconnected':
             abw=abw+int(l['bw'])
        det['vpn']['bw']=abw
        det['vpn']['branchvm']=getBranchGwVM(request, elasticnet_id)
        det['vpn']['status']='DISCONNECTED'
	res='DISCONNECTED'
	links=elasticnetclient(request).list_links(elasticnet_id)
	for l in links['links']:
	    if l['state']!='DISCONNECTED':
		res=l['state']
	det['vpn']['status']=res
	return VPN(det['vpn'])


def elasticnet_network_create(request, n_name, n_type):
    data = {'vpn': {'name': n_name, 'nettype': n_type}}
    print "++++++++ DATA = %s"%data
    print "++++++++ DATA = %s"%data
    print "++++++++ DATA Request = %s"%request
    return elasticnetclient(request).create_vpn(data)


def elasticnet_network_delete(request, n_uuid):
    return elasticnetclient(request).delete_vpn(n_uuid)


def elasticnet_network_update(request, *args):
    network_id, param_data = args
    data = {'vpn': {}}
    for kv in param_data.split(","):
        k, v = kv.split("=")
        data['vpn'][k] = v
    data['vpn']['id'] = network_id
    return elasticnetclient(request).update_vpn(network_id, data)


def elasticnet_network_details(request, n_uuid):
    details = elasticnetclient(request).show_vpn_details(n_uuid)
    return details

def elasticnet_list_sites(request, n_uuid):
    sites = elasticnetclient(request).list_sites(n_uuid)
    print "sites = %s"%sites
    ss = []
    for s in sites['sites']:
        # Get detail for this network
        #det = elasticnetclient(request).show_vpn_details(network['id'])
        print "det details %s"%s['id']
        # Get ports for this network
        #ports = elasticnetclient(request).list_ports(network['id'])
        #det['vpn']['port_count'] = len(ports['ports'])
	if not s.has_key('ip'):
	   s['ip']=''
	if not s.has_key('certificate'):
	   s['certificate']=''
        ss.append(Site({'id':s['id'], 'name':s['id'], 'keystone':s['keystone'], 'token':s['token'], 'user':s['user'], 'password':s['password'], 'tenant':s['tenant'], 'ip':s['ip'], 'certificate':s['certificate'], 'branchvm':s['branchvm'], 'state':s['state']}))
    return ss

def elasticnet_get_site(request, n_uuid, site_id):
    s1 = elasticnetclient(request).get_site(n_uuid, site_id)
    s=s1['site']
    if not s.has_key('ip'):
       s['ip']=''
    if not s.has_key('certificate'):
       s['certificate']=''
    if not s.has_key('branchvm'):
       s['branchvm']=''
    return Site({'id':s['id'], 'name':s['id'], 'keystone':s['keystone'], 'token':s['token'], 'user':s['user'], 'password':s['password'], 'tenant':s['tenant'], 'ip':s['ip'], 'certificate':s['certificate'], 'branchvm':s['branchvm'], 'state':s['state']})

def elasticnet_get_networks_in_site(request, n_uuid, remote_quantum_endpoint, token_id):
            conn1 = Connection("http://"+remote_quantum_endpoint+":9696",  "ericsson", "ericsson")
            uri1 = "/v2.0/networks"
            LOG.debug("http://"+remote_quantum_endpoint+":9696")
            LOG.debug(uri1)
            header = {}
            header["Content-Type"]= "application/json"
            header["X-Auth-Token"]= str(token_id)
            result=conn1.request_get(uri1, headers=header)
            print "+++result body=%s"%result["body"]
            body=json.loads(result["body"])
            print "+++quantum get networks body=%s"%body
            nets=body["networks"]
    	    return nets

def elasticnet_get_subnets_in_site(request, n_uuid, remoteqendpoint, tokenid):
            conn1 = Connection("http://"+remoteqendpoint+":9696",  "ericsson", "ericsson")
            uri1 = "/v2.0/subnets.json"
            LOG.debug("http://"+remoteqendpoint+":9696")
            LOG.debug(uri1)
            header = {}
            header["Content-Type"]= "application/json"
            header["X-Auth-Token"]= str(tokenid)
            result=conn1.request_get(uri1, headers=header)
            body=json.loads(result["body"])
            return body["subnets"]

def elasticnet_get_ports_in_site(request, n_uuid, remoteqendpoint, tokenid):
            conn1 = Connection("http://"+remoteqendpoint+":9696",  "ericsson", "ericsson")
            uri1 = "/v2.0/ports.json"
            LOG.debug("http://"+remoteqendpoint+":9696")
            LOG.debug(uri1)
            header = {}
            header["Content-Type"]= "application/json"
            header["X-Auth-Token"]= str(tokenid)
            result=conn1.request_get(uri1, headers=header)
            body=json.loads(result["body"])
            return body["ports"]

def elasticnet_get_token_in_site(request, n_uuid, site_id):
	  site=elasticnet_get_site(request, n_uuid, site_id)
          if False and site.token:
	    return site.token
	  else:
	    conn0 = Connection("http://"+site.keystone+":5000", "ericsson", "ericsson")
            uri0 = "/v2.0/tokens/"
            LOG.debug("http://"+site.keystone+":5000")
            LOG.debug(uri0)
            header = {}
            header["Content-Type"]= "application/json"
            jsonbody='{"auth":{"passwordCredentials":{"username":"'+str(site.user)+'", "password":"'+str(site.password)+'"}, "tenantName":"'+str(site.tenant)+'"}}'
            print "+++ result json body =%s"%jsonbody
            result=conn0.request_post(uri0, body=jsonbody, headers=header)
            print "+++ result body =%s"%result["body"]
            body=json.loads(result["body"])
            print "+++keystone get token body=%s"%body
	    tokenid=""
	    if body.has_key('access'):
		tokenid=body['access']['token']
	    return tokenid

def elasticnet_get_user_in_site(request, n_uuid, site_id):
          site=elasticnet_get_site(request, n_uuid, site_id)
          if False and site.token:
            return site.token
          else:
            conn0 = Connection("http://"+site.keystone+":5000", "ericsson", "ericsson")
            uri0 = "/v2.0/tokens/"
            LOG.debug("http://"+site.keystone+":5000")
            LOG.debug(uri0)
            header = {}
            header["Content-Type"]= "application/json"
            jsonbody='{"auth":{"passwordCredentials":{"username":"'+str(site.user)+'", "password":"'+str(site.password)+'"}, "tenantName":"'+str(site.tenant)+'"}}'
            print "+++ result json body =%s"%jsonbody
            result=conn0.request_post(uri0, body=jsonbody, headers=header)
            print "+++ result body =%s"%result["body"]
            body=json.loads(result["body"])
            print "+++keystone get USER body=%s"%body
	    user=""
	    if body.has_key('access'):
               user=body['access']['user']
            return user

	    #if body.has_key("access"): 
	#	return body['access']['token']
	#    else:
#		return None


def elasticnet_get_servers_in_site(request, n_uuid, remote_nova_endpoint, token_id, tenant_name):
          conn1 = Connection("http://"+remote_nova_endpoint+":8774",  "ericsson", "ericsson")
          uri1 = "/v2/"+tenant_name+"/servers"
	  print "$$$$$ remote_nova_endpoint="+remote_nova_endpoint
	  print "$$$$$ token_id ="+str(token_id)
          LOG.debug("http://"+remote_nova_endpoint+":8774")
          LOG.debug(uri1)
          header = {}
          header["Content-Type"]= "application/json"
          header["X-Auth-Token"]= str(token_id)
          result=conn1.request_get(uri1, headers=header)
          body=json.loads(result["body"])
	  print "$$$$ body"+str(body)
	  print "$$$$ body"+str(body)
	  print "$$$$ body"+str(body)
          return body["servers"]

 
def elasticnet_add_site(request, n_uuid, site_id, keystone=None, token=None, user=None, password=None, tenant=None, ip=None, certificate=None, branchvm=None):
    print("Operation 'add_site' executed.")
    #tenant_name, network_id, site_id  = args
    data = {'site': {'id': site_id, 'name': site_id , 'keystone':keystone, 'token':token, 'user':user, 'password':password, 'tenant':tenant, 'ip':ip, 'certificate':certificate, 'branchvm':branchvm}}
    try:
        res = elasticnetclient(request).add_site(n_uuid, data)
        new_site_id = res["site"]["id"]
    except Exception as ex:
        print "++++++++++++Exception %s"%ex #_handle_exception(ex)
    return res

def elasticnet_add_gw(request, n_uuid, site_id, gw_id):
    print("Operation 'add_gw' executed.")
    print "REQ:", request
    print "GW_ID:", gw_id
    print "Site_ID: ", site_id
    #tenant_name, network_id, site_id  = args
    data = {'gateway': {'id': gw_id, 'site': site_id, 'name': gw_id }}
    res = None
    try:
        res = elasticnetclient(request).add_gateway(n_uuid, site_id, data)
        #new_site_id = res["site"]["id"]
        #output = prepare_output("add_site", tenant_name,
        #                        dict(network_id=network_id,
        #                             site_id=new_site_id))
        #print "+++++++++++++++++%s"%output
    except Exception as ex:
        print "++++++++++++Exception %s"%ex #_handle_exception(ex)
    return res

def elasticnet_add_link(request, n_uuid, site1, gw_id1, net1, tk1, site2, gw_id2, net2, tk2,  bw):
    print("Operation 'add_link' executed.")
    data= {'sites': [{'id': site1, 'gateway':gw_id1, 'network':net1,  'token_id':tk1}, {'id': site2, 
    'gateway':gw_id2, 'network':net2,  'token_id':tk2} ], 'qos':{'bandwidth':bw} }
    #data = {'link': {'gw_id1': gw_id1, 'gw_id2': gw_id2, 'bw': bw }}
    try:
        res = elasticnetclient(request).add_link(n_uuid, data)
        #new_site_id = res["site"]["id"]
        #output = prepare_output("add_site", tenant_name,
        #                        dict(network_id=network_id,
        #                             site_id=new_site_id))
        #print "+++++++++++++++++%s"%output
    except Exception as ex:
        print "++++++++++++Exception %s"%ex #_handle_exception(ex)
    return res


def elasticnet_update_link(request, n_uuid, link_id, state, gw_id1=None, gw_id2=None, bw=None):
    print("Operation 'update_link' executed.")
    #tenant_name, network_id, site_id  = args
    #data = {'link': {'gw_id1': gw_id1, 'gw_id2': gw_id2, 'bw': bw , 'state': state}}
    data = {'state': state, 'bw':bw}
    try:
        res = elasticnetclient(request).update_link(n_uuid, link_id, data)
        #new_site_id = res["site"]["id"]
        #output = prepare_output("add_site", tenant_name,
        #                        dict(network_id=network_id,
        #                             site_id=new_site_id))
        #print "+++++++++++++++++%s"%output
    except Exception as ex:
        print "++++++++++++Exception %s"%ex #_handle_exception(ex)
    return res

def elasticnet_get_link(request, n_uuid, link_id):
    print("Operation 'get_link' executed.")
    try:
	l= elasticnetclient(request).get_link_details(n_uuid, link_id)
	l=l['link']
    except Exception as ex:
        print "++++++++++++Exception %s"%ex #_handle_exception(ex)
    return Link({'id':l['id'], 'gwid1':l['gw_id1'], 'gwid2':l['gw_id2'], 'bw':l['bw'],  'state':l['state'],  'eir':l['eir'],  'cbs':l['cbs'], 'pbs':l['pbs']})


def elasticnet_list_links(request, n_uuid):
    links = elasticnetclient(request).list_links(n_uuid)
    print "links = %s"%links
    ss = []
    for s in links['links']:
        # Get detail for this network
        #det = elasticnetclient(request).show_vpn_details(network['id'])
        print "det details %s"%s['id']
        # Get ports for this network
        #ports = elasticnetclient(request).list_ports(network['id'])
        #det['vpn']['port_count'] = len(ports['ports'])
        ss.append(Link({'id':s['id'], 'gwid1':s['gw_id1'], 'gwid2':s['gw_id2'], 'bw':s['bw'], 'state':s['state'], 'eir':s['eir'],  'cbs':s['cbs'], 'pbs':s['pbs']}))
    return ss


def elasticnet_list_gws(request, n_uuid):
    gws = elasticnetclient(request).list_gateways(n_uuid)
    print "gws = %s"%gws
    ss = []
    for s in gws['gateways']:
        # Get detail for this network
        #det = elasticnetclient(request).show_vpn_details(network['id'])
        print "det details %s"%s['id']
        # Get ports for this network
        #ports = elasticnetclient(request).list_ports(network['id'])
        #det['vpn']['port_count'] = len(ports['ports'])
        ss.append(GW({'id':s['id'], 'name':s['id'], 'site':s['site'], 'state':s['state']}))
    return ss


def elasticnet_port_list(request, n_uuid):
    q_ports = elasticnetclient(request).list_ports(n_uuid)
    ports = []
    for port in q_ports['ports']:
        # Get port details
        det = elasticnetclient(request).show_port_details(n_uuid, port['id'])
        att = elasticnetclient(request).show_port_attachment(n_uuid, port['id'])
        # Get server name from id
        if 'id' in att['attachment']:
            server = get_interface_server(request, att['attachment']['id'])
            #det['port']['attachment_server'] = server.name
            det['port']['attachment_server'] = server
            det['port']['attachment_id'] = att['attachment']['id']
        else:
            det['port']['attachment_id'] = None
            det['port']['attachment_server'] = None
        ports.append(Port(det['port']))
    return ports


def elasticnet_port_create(request, num, uuid):
    for i in range(int(num)):
        elasticnetclient(request).create_port(uuid)


def elasticnet_port_delete(request, n_uuid, p_uuid):
    return elasticnetclient(request).delete_port(n_uuid, p_uuid)


def elasticnet_port_update(request, *args):
    tenant_name, network_id, port_id, param_data, version = args
    data = {'port': {}}
    for kv in param_data.split(","):
        k, v = kv.split("=")
        data['port'][k] = v
    data['network_id'] = network_id
    data['port']['id'] = port_id

    return elasticnetclient(request).update_port(network_id, port_id, data)


def elasticnet_port_attach(request, network_id, port_id, attachment):
    data = {'attachment': {'id': '%s' % attachment}}

    return elasticnetclient(request).attach_resource(network_id, port_id, data)


def elasticnet_port_detach(request, network_id, port_id):
    return elasticnetclient(request).detach_resource(network_id, port_id)


def elasticnet_ports_toggle(request, network_id, port_id, state):
    data = {'port': {'state': state}}
    return elasticnetclient(request).update_port(network_id, port_id, data)


def get_free_interfaces(request):
    instance_interfaces = []
    attached_interfaces = []
    # Fetch a list of networks
    networks = elasticnet_network_list(request)
    for network in networks:
        # Get all ports
        ports = quantum_port_list(request, network.id)
        for port in ports:
            # Check for attachments
            if port.attachment_id:
                attached_interfaces.append(port.attachment_id)

    # Get all instances
    instances = nova.server_list(request)
    for instance in instances:
        vifs = nova.virtual_interfaces_list(request, instance.id)
        for vif in vifs:
            if not any(vif.id in s for s in attached_interfaces):
                instance_interfaces.append(
                {'instance': instance.name, 'vif': vif.id})
    return instance_interfaces


def get_interface_server(request, interface):
    # Get all instances
    instances = nova.server_list(request)
    for instance in instances:
        vifs = nova.virtual_interfaces_list(request, instance.id)
        for vif in vifs:
            if vif.id == interface:
                return instance
    return None
