#!/bin/bash

# git clone https://github.com/kimcharli/apstra-api.git
# cd apstra-api
brew install python3.9
python3 -m venv venv
source venv/bin/activate
pip install -r python/requirements.txt 
deactivate 

