#!/usr/bin/env python

from cloudify import ctx
from cloudify.exceptions import OperationRetry
from cloudify.state import ctx_parameters as inputs
from cloudify_rest_client.exceptions import CloudifyClientError
from requests.exceptions import ConnectionError
from cloudify.manager import get_rest_client


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
        else:
            ctx.logger.error('Ignoring error: {0}'.format(str(e)))
    else:
        ctx.logger.debug('Returning response: {0}'.format(response))
        return response
    return None


if __name__ == '__main__':

    # Set the client.
    client = get_rest_client(
        tenant=ctx.instance.runtime_properties.get('examples_tenant_name', 'examples'))

    # Check if plugins are uploaded.
    for plugin_id in ctx.instance.runtime_properties.get('plugin_ids', []):
        check_api(client.plugins.delete, plugin_id)

    for secret_key in ctx.instance.runtime_properties.get('secret_keys', []):
        check_api(client.secrets.delete, secret_key)
