#!/bin/bash

# https://github.com/bobbyiliev/introduction-to-bash-scripting
rm db.sqlite3
python manage.py migrate
python manage.py loaddata datas
python manage.py creategenesisevent

# to run $ `bash run.sh`