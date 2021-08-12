#!/bin/bash

# git clone https://github.com/kimcharli/apstra-api.git
# cd apstra-api
sudo apt update
sudo apt -y install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt -y install python3.7 python3.7-distutils
virtualenv -p python3.7 venv
source venv/bin/activate
pip install -r python/requirements.txt 
deactivate 
