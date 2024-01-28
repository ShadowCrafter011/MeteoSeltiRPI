ping -c4 192.168.1.1 > /dev/null

if [ $? != 0 ]
then
  echo "No network connection, restarting"
  sudo shutdown -r now
fi
