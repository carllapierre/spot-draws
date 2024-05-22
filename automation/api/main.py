from application.app import app  # pylint: disable=unused-import

# Init all routes, this starts the web listeners
from application.gateway.http import init_routes

init_routes()

# Init services
from application.services import init_services

init_services()
