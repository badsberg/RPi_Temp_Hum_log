NOW=$(date +"%D-%H:%M:%S") 
if ping -c 1 www.google.com | grep '1 received' ; then
    echo $NOW  "Network connection running" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
else
    echo $NOW  "Network connection down! Attempting reconnection." >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo ifdown wlan0
    sleep 10
    sudo ifup --force wlan0
    sleep 
    ping -c 1 www.google.com >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo ifup -a
    #sudo ifup --force wlan0 >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo dhclient >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo /etc/init.d/networking restart
fi

