docker exec -it gkbot-api ifconfig eth0 | grep 'inet addr' | sed -e 's/:/ /' | awk '{print $3}'
