import traceback
import time
from time import mktime
from datetime import datetime
from requests.auth import HTTPBasicAuth
from oslo_log import log as logging

from django.template.defaultfilters import register
from django.utils.translation import ugettext_lazy as _
import requests, json

from horizon import exceptions

LOG = logging.getLogger(__name__)

data = json.dumps({'name':'test', 'description':'some test repo'})
url = 'http://127.0.0.1:7007/deploy_service'
remove_url = 'http://127.0.0.1:7007/delete_service'
def deployApp(app):
    try:
	LOG.debug("APP which is getting deployed is: {0}".format(app))
        payload = {'vnf_name': app['name'],
                   'branch_name' : app['branchName'],
                   'tenant_name' : "T-Labs:Mtn-Vw",
                   'vnf_services': [{'name': app['name'],'image': app['url']}]
                  }
        LOG.debug("payload: {0}".format(payload))
        headers = {'content-type': 'application/json'}
        req = requests.post(url, data=json.dumps(payload), headers = headers)
    except:
        LOG.debug("Exception occurred at deployApps")
        return False

def deleteApp(app):
    try:
        LOG.debug("APP which is getting deleted is: {0}".format(app))
        payload = {'vnf_name': app['vnf_name'],
                   'branch_name' : app['branch_name'],
                   'tenant_name' : "T-Labs:Mtn-Vw",
                   'vnf_services': [{'name': app['vnf_name'],'image': app['url']}]
                  }
        LOG.debug("payload: {0}".format(payload))
        headers = {'content-type': 'application/json'}
        req = requests.post(remove_url, data=json.dumps(payload), headers = headers)
    except:
        LOG.debug("Exception occurred at deployApps")
        return False
