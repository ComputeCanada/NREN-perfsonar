# perfsonar scripts to upload into elasticsearch and other useful scripts

This repo contains a collection of scripts to upload data into an elasticsearch instance and
additionally some other useful scripts for monitoring and maintaining perfsonar servers.

## Uploading data into an elasticsearch databases
To allow for monitoring and alarming, one possible way is to upload all collected data into
an elasticsearch instance and process the data there. THe data can then be displayed via
kibana or via grafana dashboards.

Since some processing of the data needs to be done to transform it into something easier
to handle by elasticsearch, we decided to collect data locally on the perfsonar node
via a python script and upload into a remote instance of elasticsearch. These scripts
are still in development, also because not everything can be displayed in elasticsearch
/ kibana yet, so likely some modifications are still needed. The uploaded data however
should be very close to being complete, we didn't bother uploading summaries like
histograms of other data that is being uploaded.

### Usage
These scripts started on SLC6 hosts, where only python2.6 was available. Therefore,
we used software collections to install a newer python2.7 environment. This is still
included, but commented in the current run scripts.

To install a cron job, add this to your crontab:
```
1,16,31,46 * * * * cd $HOME/es_upload/esmond-py; ./run_cron_bw.sh
```
Using the wrapper script, you will get a check that the run time of the script is
under control, as well as get some debugging output for all uploads in the last 24 hours.


## Collection of useful scripts
At the time of writing only one scipt is there, which needs to be run from the root
account, as it collects information that only the administrator account can collect.
It also reboots the perfsonar server if a newer kernel is available for more than
one week - to allow the maintainer to choose a good time to reboot, but keep the
machine secure if the maintainer is unavailable for an extended period of time.

Daily emails are sent about the status of the server, which include diskspace,
the latest yum update, and other system information.

### Usage
This script is supposed to be installed and run as root once a day per cron. E.g.
```
0 23 * * * /root/check.sh
```
will run it 23 minutes past midnight. Choose whatever time is convenient to receive
these emails.