import httpx


def default_httpx_client_opt_generator():
    return {
        'timeout': httpx.Timeout(10.0),
        'transport': httpx.AsyncHTTPTransport(retries=5)
    }
