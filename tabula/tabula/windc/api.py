# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from portasclient.v1.client import Client as windc_client

log = logging.getLogger(__name__)


def windcclient(request):
    url = "http://127.0.0.1:8082"
    log.debug('windcclient connection created using token "%s" and url "%s"'
              % (request.user.token, url))
    return windc_client(endpoint=url, token=request.user.token.token['id'])


def datacenters_create(request, parameters):
    env = windcclient(request).environments.create(parameters.get('name', ''))
    log.debug('Environment::Create {0}'.format(env))
    return env


def datacenters_delete(request, datacenter_id):
    result = windcclient(request).environments.delete(datacenter_id)
    log.debug('Environment::Delete Id:{0}'.format(datacenter_id))
    return result


def datacenters_get(request, datacenter_id):
    env = windcclient(request).environments.get(datacenter_id)
    log.debug('Environment::Get {0}'.format(env))
    return env


def datacenters_list(request):
    log.debug('Environment::List')
    return windcclient(request).environments.list()


def datacenters_deploy(request, datacenter_id):
    sessions = windcclient(request).sessions.list(datacenter_id)
    for session in sessions:
        if session.state == 'open':
            session_id = session.id
    if not session_id:
        return "Sorry, nothing to deploy."
    log.debug('Obtained session with Id: {0}'.format(session_id))
    result = windcclient(request).sessions.deploy(datacenter_id, session_id)
    log.debug('Environment with Id: {0} deployed in session '
              'with Id: {1}'.format(datacenter_id, session_id))
    return result


def services_create(request, datacenter, parameters):
    session_id = None
    sessions = windcclient(request).sessions.list(environment_id)

    for s in sessions:
        if s.state == 'open':
            session_id = s.id
        else:
            windcclient(request).sessions.delete(environment_id, s.id)

    if session_id is None:
        session_id = windcclient(request).sessions.configure(environment_id).id

    if parameters['service_type'] == 'Active Directory':
        service = windcclient(request)\
            .activeDirectories\
            .create(datacenter, session_id, parameters)
    else:
        service = windcclient(request)\
            .webServers.create(datacenter, session_id, parameters)

    log.debug('Service::Create {0}'.format(service))
    return service


def get_time(obj):
    return obj.updated


def services_list(request, datacenter_id):
    session_id = None
    sessions = windcclient(request).sessions.list(datacenter_id)
    for s in sessions:
        session_id = s.id

    if session_id is None:
        session_id = windcclient(request).sessions.configure(datacenter_id).id

    services = windcclient(request).activeDirectories.list(datacenter_id,
                                                           session_id)
    services += windcclient(request).webServers.list(datacenter_id, session_id)

    for i in range(len(services)):
        reports = windcclient(request).sessions. \
            reports(datacenter_id, session_id,
                    services[i].id)

        for report in reports:
            services[i].operation = report.text

    log.debug('Service::List')
    return services


def get_active_directories(request, datacenter_id):
    session_id = None
    sessions = windcclient(request).sessions.list(datacenter_id)

    for s in sessions:
        session_id = s.id

    if session_id is None:
        session_id = windcclient(request).sessions.configure(datacenter_id).id

    services = windcclient(request)\
        .activeDirectories\
        .list(datacenter_id, session_id)

    log.debug('Service::Active Directories::List')
    return services


def services_get(request, datacenter_id, service_id):
    services = services_list(request, datacenter_id)

    for service in services:
        if service.id == service_id:
            log.debug('Service::Get {0}'.format(service))
            return service


def get_data_center_id_for_service(request, service_id):
    datacenters = datacenters_list(request)

    for dc in datacenters:
        services = services_list(request, dc.id)
        for service in services:
            if service.id == service_id:
                return dc.id


def get_service_datails(request, service_id):
    datacenters = datacenters_list(request)
    services = []
    for dc in datacenters:
        services += services_list(request, dc.id)

    for service in services:
        if service.id == service_id:
            return service


def get_status_message_for_service(request, service_id):
    environment_id = get_data_center_id_for_service(request, service_id)
    session_id = None
    sessions = windcclient(request).sessions.list(environment_id)

    for s in sessions:
        session_id = s.id

    if session_id is None:
        session_id = windcclient(request).sessions.configure(environment_id).id

    reports = windcclient(request).sessions. \
        reports(environment_id, session_id, service_id)

    result = 'Initialization.... \n'
    for report in reports:
        result += '  ' + str(report.text) + '\n'

    return result


def services_delete(request, datacenter_id, service_id):
    log.debug('Service::Remove EnvId: {0} '
              'SrvId: {1}'.format(datacenter_id, service_id))

    services = services_list(request, datacenter_id)

    session_id = None
    sessions = windcclient(request).sessions.list(datacenter_id)
    for session in sessions:
        if session.state == 'open':
            session_id = session.id

    if session_id is None:
        raise Exception("Sorry, you can not delete this service now.")

    for service in services:
        if service.id is service_id:
            if service.type is 'Active Directory':
                windcclient(request).activeDirectories.delete(datacenter_id,
                                                              session_id,
                                                              service_id)
            elif service.type is 'IIS':
                windcclient(request).webServers.delete(datacenter_id,
                                                       session_id,
                                                       service_id)
