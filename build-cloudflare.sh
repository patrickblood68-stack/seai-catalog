#!/bin/sh
set -eu

mkdir -p dist
cp public/index.html catalog.json llms.txt llms-full.txt dist/
cp -R data schemas inventory dist/
