#!/bin/bash
#More about users: https://docs.perfsonar.net/pwa_user_management.html
#To enable email signup see: https://docs.perfsonar.net/pwa_configure.html#authentication-service-sca-auth
echo -n "Enter desired username and press [ENTER]: "
read user
echo -n "Enter desired password and press [ENTER]: "
read passwd
echo -n "Enter full name and press [ENTER]: "
read name
echo -n "Enter email and press [ENTER]: "
read email
echo "Adding user: $user to admins..."
docker exec sca-auth /app/bin/auth.js useradd --username $user --fullname "$name" --email "$email" [--password "$passwd"]
docker exec sca-auth /app/bin/auth.js modscope --username $user --add '{"pwa": ["user", "admin"]}'
docker exec sca-auth /app/bin/auth.js setpass --username $user --password "$passwd"
