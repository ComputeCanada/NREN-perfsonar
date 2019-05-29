#!/bin/bash -l
#exit(0)
# source /opt/rh/python27/enable
/usr/bin/time ./iperf.py > ipbw.log-$(date "+%H-%M") 2>&1

