from application.app import app  # pylint: disable=unused-import

# Init all routes, this starts the web listeners
from application.gateway.http import init_routes

if __name__ == "wsgi":
    init_routes()
