#! /usr/bin/env bash
set -e -x

# copy
mkdir -p ./blog
pwd
cp -r ../pages/* ./blog/

# cleanup
find ./blog/ -name '.keep' -delete
find ./blog/ -name '.git' -delete

# rename
find ./blog/ -type f -exec sed -i "s|${BASE_URL}|https://${FALLBACK_URL}|g" {} +
find ./blog/ -type f -exec sed -i "s|https://${TRACKING}|${TRACKING_FALLBACK}|g" {} +

# upload
.,/,venv/bin/python neocities_upload.py
