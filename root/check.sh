#!/bin/bash

MAILTO="anonymous@where.ca"

BI=$(ls -ltr /boot/vm* | grep -v rescue | tail -1)
UN=$(uname -r)
YL=$(ls -l /var/log/yum.log)
YA=$(stat --format="%Z" /var/log/yum.log)
LW=$(date "+%s" -d "last week")
DF=$(lsblk -l -o MOUNTPOINT -n | grep "^/")
DF=$(df $DF)
UT=$(uptime)
DB=$(/usr/sbin/dmidecode -q -t bios | head -4)
DS=$(/usr/sbin/dmidecode -q -t system | head -3)
MD=$(md5sum /root/check.sh)
H=$(hostname -s)
M="MPS: $H mismatched kernels"
if ls -tr1 /boot/vm* | grep -v rescue | tail -1 | grep -q -w $(uname -r) ; then
  M="MPS: $H OK"
fi
if [[ $LW -gt $YA ]]; then
    M="$M - yum update over a week ago"
fi
YC=$(systemctl status yum-cron.service || systemctl restart yum-cron.service )
N=${BI#*vmlinuz-}
STR="\nLatest kernel available:\n$BI\nand is running: good !\n"
if [ "x$UN" != "x$N" ]; then
    STR="\nLatest kernel available:\n$BI\nbut running:\n    $UN\n != $N\n"
fi
NR=$(needs-restarting -r)
NRRC=$?
REBOOT=false
if [[ "$NRRC" -eq "0" ]]; then
    rm -f /tmp/restart
else
    CDR=0
    if [ -f /tmp/restart ]; then
        CDR=$(cat /tmp/restart)
    fi
    ((CDR ++))
    echo "$CDR" > /tmp/restart
    if [[ "$CDR" -gt "7" ]]; then
        NR="$NR\n\n   OLDER THAN 7 DAYS - WILL RESTART NOW !\n"
        REBOOT=true
    fi
fi
/bin/echo -e "$STR\nLast yum update done:\n$YL\n" \
          "\nReboot required:\n$NR\n\n$YC\n\nFree disk space\n$DF\n\nuptime:\n$UT\n" \
          "\n$DB\n\n$DS\n\n$MD\n" | mail -s "$M" "$MAILTO"

if $REBOOT ; then
    rm -f /tmp/restart
    # wait 5 mins to clear mailqueue
    sleep 5m
    /sbin/reboot
fi

