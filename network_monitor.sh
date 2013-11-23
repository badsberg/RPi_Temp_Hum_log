NOW=$(date +"%D-%H:%M:%S") 
if  ping -c 4 192.168.1.1  >/dev/null ; then
    echo $NOW  "Network connection up!" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo iwlist wlan0 scan | grep -e "Quality" -e "ESSID" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
else
    echo $NOW  "Network connection down!" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo ifdown wlan0 
    #sleep 5
    #sudo ifup --force wlan0 
    #sleep 5
    
    sudo ifup -a
    sleep 5
    #sudo ifup --force wlan0 >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo dhclient
    #ping -c 1 www.google.com >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #ping -c 1 192.168.1.1 >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo /etc/init.d/networking restart
fi
