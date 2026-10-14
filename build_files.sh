#!/bin/bash
# Build script for Vercel deployment
echo "Building project..."
python3 -m pip install --break-system-packages -r requirements.txt
python3 manage.py collectstatic --noinput --clear
