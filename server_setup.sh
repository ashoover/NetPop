#!/bin/bash
host_name = "netpop"

# Install python3 venv & pip stuff
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv

# Make app dir
mkdir -p ~/app/NetPop 

# Make python3 venv
cd ~/app/NetPop_venv
python3 -m venv netpop_venv

# Get current software from repo
mkdir netpop_app
cd netpop_app
git clone https://github.com/ashoover/netpop

# Install Nginx & fw ports on local box
sudo apt-get install nginx
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'

# Install python3 requirements.txt
source ~/app/NetPop_venv/netpop/bin/activte
pip install --requirement requirements.txt
pip install gunicorn