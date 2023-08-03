#!/usr/bin/env bash
set -x -e

echo "building front end for kbgpt"

cd kbgpt/fe

npm cache clean --force
npm install --unsafe-perm=true --allow-root
npm run build