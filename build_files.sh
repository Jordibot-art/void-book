#!/bin/bash
# Build script for Vercel deployment
echo "Building project..."
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
