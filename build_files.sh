#!/bin/bash
# Build script for Vercel deployment
set -e
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-vercel.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
