from glob import glob
from importlib import import_module
from os.path import basename, dirname, isfile, join


def init_services():
    """
    Initializes all services in the system.
    """

    # Get the files within the `services` directory that ends with .py
    services = glob(join(dirname(__file__), "./services/*.py"))

    # Import all python files in the `application/web/services/` directory.
    for service_file in services:
        # Make sure it is a file and not an init file.
        if isfile(service_file) and not service_file.endswith("__init__.py"):
            file_name = basename(service_file[:-3])  # remove `.py` from the name

            # Import service.
            import_module(".{0}".format(file_name), "application.services")
