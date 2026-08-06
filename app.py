import os

from Presentation.app import app


if __name__ == "__main__":
    debug = os.getenv("APP_DEBUG", "false").lower() == "true"
    app.run(host=os.getenv("APP_HOST", "127.0.0.1"), port=int(os.getenv("APP_PORT", "8080")), debug=debug, reloader=debug)
