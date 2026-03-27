#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py makemigrations dashboard --no-input

python manage.py migrate dashboard --fake-initial --no-input
python manage.py collectstatic --no-input