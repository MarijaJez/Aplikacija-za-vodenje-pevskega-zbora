import os

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
