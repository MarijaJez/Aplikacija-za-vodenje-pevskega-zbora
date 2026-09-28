import os

if os.getenv("GOOGLE_FORCE_IPV6", "false").lower() == "true":
    # This host can reach Google over IPv6, while IPv4 HTTPS connections time out.
    # All outbound requests in this app currently target Google APIs.
    import socket
    from urllib3.util import connection as urllib3_connection

    urllib3_connection.allowed_gai_family = lambda: socket.AF_INET6

from Presentation.app import app
from waitress import serve


if __name__ == "__main__":
    debug = os.getenv("APP_DEBUG", "false").lower() == "true"
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8091"))
    if debug:
        app.run(host=host, port=port, debug=True, reloader=True)
    else:
        serve(app, host=host, port=port, threads=4)
