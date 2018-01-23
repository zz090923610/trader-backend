#!/usr/bin/env bash
apt-get update
apt-get install -y python3-pip mosquitto mosquitto-clients
pip3 install selenium paho-mqtt pytz requests beautifulsoup4 lxml pandas pillow
pip3 install tushare