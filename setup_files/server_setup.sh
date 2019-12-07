#!/bin/bash
host_name = "netpop"

# Install python3 venv & pip stuff
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv -y

# Make app dir
mkdir -p ~/app/NetPop 

# Setup and make python3 venv
cd ~/app/NetPop/

# Get current software from repo and move to correct dir
mkdir ~/app/NetPop/netpop_app -p
cd ~/app/NetPop/netpop_app
git clone https://github.com/ashoover/netpop
mv netpop/* .

# Install Nginx & fw ports on local box
sudo apt-get install nginx -y
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'

# Install python3 requirements.txt into the venv
pip3 install virtualenvwrapper

export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
#export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.7 # might be needed for some RPi
source ~/.local/bin/virtualenvwrapper.sh

cd ~/app/NetPop/netpop_app
mkvirtualenv -a . -r requirements.txt netpop_venv

# Messages
echo "##########################################################################"
echo "#"
echo "#  Installation Complete"
echo "#  Don't forget to edit ~/app/NetPop/netpop_app/dbconfig.py with your info"
echo "#  Settings for the web front end are in ~/app/NetPop/netpop_app/conf/config.ini"
echo "#"
echo "##########################################################################"
