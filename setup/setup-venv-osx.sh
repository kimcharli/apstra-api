#!/bin/bash

# git clone https://github.com/kimcharli/apstra-api.git
# cd apstra-api
brew install python3

python3 -m venv python/venv
. python/venv/bin/activate
pip install -r python/requirements.txt 
deactivate 

python3 -m venv ansible/venv
. ansible/venv/bin/activate
pip install -r ansible/requirements.txt 
deactivate 

