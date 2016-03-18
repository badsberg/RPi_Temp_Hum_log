NOW=$(date +"%D-%H:%M:%S") 
if  ping -c 4 192.168.0.1  >/dev/null ; then
    echo $NOW  "Network connection up!" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo iwlist wlan0 scan | grep -e "Quality" -e "ESSID" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
else
    echo $NOW  "Network connection down!" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo iwlist wlan0 scan | grep -e "Quality" -e "ESSID" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo ifup -a
    sleep 5
    sudo dhclient
    NOW=$(date +"%D-%H:%M:%S") 
    echo $NOW  "Network established!" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
fi
/opt/vc/bin/vcgencmd measure_temp >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
