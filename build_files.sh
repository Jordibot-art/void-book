#!/bin/bash
# Build script for Vercel deployment
set -e
echo "Installing dependencies..."
pip install --break-system-packages --upgrade pip
pip install --break-system-packages -r requirements-vercel.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
