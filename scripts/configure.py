#!/usr/bin/env python

from cloudify import ctx
from cloudify.exceptions import OperationRetry
from cloudify.state import ctx_parameters as inputs
from cloudify_rest_client.exceptions import CloudifyClientError
from requests.exceptions import ConnectionError
from cloudify.manager import get_rest_client


class SecretNotFoundError(Exception):
    pass


def check_api(client_callable, arguments=None, _progress_handler=None):
    """ Check for API Response and handle generically. """

    try:
        if isinstance(arguments, dict):
            response = client_callable(**arguments)
        elif arguments is None:
            response = client_callable()
        elif _progress_handler is not None:
            response = client_callable(
                arguments, progress_callback=_progress_handler)
        else:
            response = client_callable(arguments)
    except ConnectionError as e:
        raise OperationRetry('Retrying after error: {0}'.format(str(e)))
    except CloudifyClientError as e:
        if e.status_code == 502:
            raise OperationRetry('Retrying after error: {0}'.format(str(e)))

        if e.status_code == 404:
            raise SecretNotFoundError('Not Found error {0}'.format(str(e)))

        else:
            ctx.logger.error('Ignoring error: {0}'.format(str(e)))
    else:
        ctx.logger.debug('Returning response: {0}'.format(response))
        return response
    return None


if __name__ == '__main__':

    # Set script-wide variables from inputs.
    examples_tenant_name = inputs.get('tenant', 'examples')
    ctx.instance.runtime_properties['examples_tenant_name'] = examples_tenant_name
    examples_plugins_urls = inputs.get('plugins', [])
    examples_secrets = inputs.get('secrets', {})

    # Set the client.
    client = get_rest_client()

    # Make sure the examples tenant exists.
    tenant = check_api(client.tenants.get, examples_tenant_name)
    if tenant is None:
        check_api(client.tenants.create, examples_tenant_name)
    client = get_rest_client(tenant=examples_tenant_name)

    # Check if plugins are uploaded.
    for plugin_url in examples_plugins_urls:
        output = check_api(client.plugins.upload, plugin_url)
        try:
            plugin_id = output['id']
            plugin_ids = ctx.instance.runtime_properties.get('plugin_ids', [])
            plugin_ids.append(plugin_id)
            ctx.instance.runtime_properties['plugin_ids'] = plugin_ids
        except KeyError:
            ctx.logger.error('KeyError for plugin ID.')

    # Check if secrets exist.
    for secret_key in examples_secrets.keys():
        ks = ctx.instance.runtime_properties.get('secret_keys', [])
        ks.append(secret_key)
        ctx.instance.runtime_properties['secret_keys'] = ks
        secret = None
        try:
            secret = check_api(client.secrets.get,
                               arguments={'key': secret_key})
            if secret:
                check_api(
                    client.secrets.update,
                    arguments={'key': secret_key,
                               'value': examples_secrets[secret_key]})

        except SecretNotFoundError:
            new_secret = check_api(
                client.secrets.create,
                arguments={'key': secret_key,
                           'value': examples_secrets[secret_key]})

