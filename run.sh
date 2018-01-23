#!/bin/bash
service mosquitto start
export LANG=en_US.UTF-8
cd /root/trader-backend && python3 -m TradeDaemon