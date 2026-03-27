#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --fake dashboard zero --no-input

python manage.py makemigrations dashboard --no-input
python manage.py migrate --no-input
python manage.py collectstatic --no-input