#!/bin/bash
uwsgi --socket 0.0.0.0:8000 --protocol=http --manage-script-name --mount /=wsgi:app
