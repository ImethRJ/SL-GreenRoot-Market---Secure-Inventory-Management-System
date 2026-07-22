#!/bin/bash
# Install Python dependencies using active python runtime
python3 -m pip install -r requirements.txt

# Build static minified Tailwind CSS
npx -y tailwindcss@3 -i ./inventory/static/css/input.css -o ./inventory/static/css/tailwind.css --minify

# Collect static files for Django
python3 manage.py collectstatic --no-input --clear
