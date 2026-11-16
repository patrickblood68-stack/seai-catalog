#!/bin/sh
set -eu

mkdir -p dist
cp public/404.html public/robots.txt llms.txt llms-full.txt dist/
cp -R data schemas inventory dist/
python3 render_public_guides.py
