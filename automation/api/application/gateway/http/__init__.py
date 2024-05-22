import json
from functools import wraps
from glob import glob
from importlib import import_module
from os.path import basename, dirname, isfile, join
from typing import Any, Callable, List

from flask import make_response


def init_routes():
    """
    Initializes all the routes in the system.
    """

    # Get the files within the `routes` directory that ends with .py
    routes = glob(join(dirname(__file__), "./routes/*.py"))

    # Import all python files in the `application/web/routes/` directory.
    for route_file in routes:
        # Make sure it is a file and not an init file.
        if isfile(route_file) and not route_file.endswith("__init__.py"):
            file_name = basename(route_file[:-3])  # remove `.py` from the name

            # Import route.
            import_module(f".{file_name}", "application.gateway.http.routes")
