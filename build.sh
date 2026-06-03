#!/bin/bash
set -e
cd /Users/panzj/feiyanggit/ha-esp32max/esp32HA-max/app/feyagate-skill-gh
rm -rf dist/
python3 -m build
python3 -m twine upload dist/*