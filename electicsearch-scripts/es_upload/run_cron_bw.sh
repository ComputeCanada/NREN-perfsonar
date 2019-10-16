#!/bin/bash -l
# following was needed to run python27 on rhel6:
# source /opt/rh/python27/enable

# recommended for most indices, to easily allow deletion of old indices based on year, month or
#  similar metrices, week or day of year for example
export ELASTIC_WEB_BASE="https://<your_ES_instance>:<port>/<your_index>_$(date "+%y-%m")-"
export ELASTIC_WEB_PASS="<your_username>:<your_passwd>"
/usr/bin/time ./iperf.py > ipbw.log-$(date "+%H-%M") 2>&1


