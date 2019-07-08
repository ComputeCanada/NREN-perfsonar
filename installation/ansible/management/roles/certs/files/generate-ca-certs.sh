#!/bin/bash
YELLOW='\033[1;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

printf "${YELLOW}\nWelcome! We will now try to generate CA approved certificates and add a new cert-renewing cronjob.\n\n${NC}"
read -p "Press enter to continue..."

certbot --apache && \
certbot renew --dry-run && \
echo "0 0,12 * * * python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew" \
>> /etc/crontab && systemctl restart crond.service && \
systemctl restart httpd && \
printf "${GREEN}\nCongratulations everything seems to be working!\n\n${NC}"\
|| printf "${RED}\nProcedure failed, please try again...\n\n${NC}"
