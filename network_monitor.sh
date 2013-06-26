NOW=$(date +"%D-%H:%M:%S") 
if  ping -c 1 www.google.com  >/dev/null ; then
    echo $NOW  "Network connection running" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
else
    echo $NOW  "Network connection down! " >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo ifdown wlan0 
    sleep 5
    sudo ifup --force wlan0 
    sleep 5
    ping -c 1 www.google.com >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    ping -c 1 192.168.1.1 >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo ifup -a
    #sudo ifup --force wlan0 >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo dhclient >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    #sudo /etc/init.d/networking restart
fi
