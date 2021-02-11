#!/usr/bin/env bash
# start nginx
sudo nginx
# start uwsgi
uwsgi --ini VariantViewer_uwsgi.ini