"""API object handling communication with asmaster, for use in manager mode."""

from __future__ import absolute_import

import time
import requests

from . import utils
from .conf import settings


class AsmasterApi(object):
    """Primary object that pushes requests into a distinct stream thread."""

    def __init__(self, timeout):
        self.timeout = timeout
        self.host = settings.get('hosts', 'asmaster_host')
        self.token = settings.get('auth', 'token')

        self.list_services_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'list_services'))
        self.list_subscriptions_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'list_subscriptions'))
        self.subscribe_account_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'subscribe_account'))
        self.perform_2fa_challenge_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'perform_2fa_challenge'))
        self.submit_2fa_challenge_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'submit_2fa_challenge'))
        self.list_devices_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'list_devices'))
        self.subscribe_device_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'subscribe_device'))
        self.resubscribe_account_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'resubscribe_account'))
        self.unsubscribe_device_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'unsubscribe_device'))
        self.unsubscribe_account_endpoint = '%s%s' % (self.host, settings.get('asmaster_endpoints', 'unsubscribe_account'))

        self.services = {}

    @property
    def token_header(self):
        return {
            'Authorization': 'Token %s' % self.token,
        }

    def _get_info(self):
        """Fetch account information from ASApi host."""
        return self._perform_get_request(self.list_services_endpoint, headers=self.token_header)

    @staticmethod
    def _parse_endpoint(endpoint):
        """Expect endpoint to be dictionary containing `protocol`, `host` and `uri` keys."""
        return "{protocol}://{host}{uri}".format(**endpoint)

    def _set_endpoints(self, info):
        self.stream_endpoints = info['stream_endpoints']

    def _set_allowed_services_and_actions(self, services):
        """Expect services to be a list of service dictionaries, each with `name` and `actions` keys."""
        for service in services:
            self.services[service['name']] = {}

            for action in service['actions']:
                name = action.pop('name')
                self.services[service['name']][name] = action

    def setup(self):
        info = self._get_info()
        self._set_endpoints(info)
        self.retrieval_protocol = None
        self._set_allowed_services_and_actions(info['services'])

    def allowed_services(self):
        return self.services.keys()

    def allowed_actions(self, service_name):
        return self.services[service_name].keys()

    def list_subscriptions(self, service):
        """Asks for a list of all subscribed accounts and devices, along with their statuses."""
        data = {
            'service': service,
        }
        return self._perform_post_request(self.list_subscriptions_endpoint, data, self.token_header)

    def subscribe_account(self, username, password, service):
        """Subscribe an account for a service.
        """
        data = {
            'service': service,
            'username': username,
            'password': password,
        }

        return self._perform_post_request(self.subscribe_account_endpoint, data, self.token_header)

    def perform_2fa_challenge(self, account_id, device_id):
        data = {
            'account_id': account_id,
            'device_id': device_id,
        }
        return self._perform_post_request(self.perform_2fa_challenge_endpoint, data, self.token_header)

    def submit_2fa_challenge(self, account_id, code):
        data = {
            'account_id': account_id,
            'code': code,
        }
        return self._perform_post_request(self.submit_2fa_challenge_endpoint, data, self.token_header)

    def resubscribe_account(self, account_id, password):
        data = {
            'account_id': account_id,
            'password': password,
        }

        return self._perform_post_request(self.resubscribe_account_endpoint, data, self.token_header)

    def unsubscribe_account(self, account_id):
        data = {
            'account_id': account_id,
        }

        return self._perform_post_request(self.unsubscribe_account_endpoint, data, self.token_header)

    def list_devices(self, account_id):
        data = {
            'account_id': account_id,
        }

        return self._perform_post_request(self.list_devices_endpoint, data, self.token_header)

    def subscribe_device(self, account_id, device_id):
        data = {
            'account_id': account_id,
            'device_id': device_id,
        }

        return self._perform_post_request(self.subscribe_device_endpoint, data, self.token_header)

    def unsubscribe_device(self, account_id, device_id):
        data = {
            'account_id': account_id,
            'device_id': device_id,
        }

        return self._perform_post_request(self.unsubscribe_device_endpoint, data, self.token_header)

    @staticmethod
    def _parse_response(response, post_request=False):
        """Treat the response from ASApi.

        The json is dumped before checking the status as even if the response is
        not properly formed we are in trouble.
        """
        data = response.json()

        if not response.ok:
            utils.error_message_and_exit('Asmaster Api Error:', data)

        if post_request and not data['success']:
            raise Exception('Asmaster Api Error: [%s]' % data['error'])

        return data

    def _perform_get_request(self, url, headers=None):
        response = requests.get(
            url,
            headers=headers,
            timeout=self.timeout,
        )
        return self._parse_response(response)
    
    def _perform_post_request(self, url, data, headers=None):
        response = requests.post(
            url,
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        return self._parse_response(response, post_request=True)
