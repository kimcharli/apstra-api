#!/bin/bash

# git clone https://github.com/kimcharli/apstra-api.git
# cd apstra-api
sudo apt update
sudo apt -y install software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt -y install python3.7 python3.7-distutils python3-venv

virtualenv -p python3.7 ansible/venv
. ansible/venv/bin/activate
pip install -r ansible/requirements.txt 
deactivate 
