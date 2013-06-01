NOW=$(date +"%D-%H:%M:%S") 
#date +%D-%H:%M:%S >> /home/pi/RPi_Temp_Hum_log
if sudo ping -c 1 192.168.1.1 | grep '1 received' >> /home/pi/RPi_Temp_Hum_log/network_monitor.log ; then
    echo $NOW  "Network connection running" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
else
    echo $NOW  "Network connection down! Attempting reconnection." >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
    sudo ifup --force wlan0
fi
#sudo ifconfig wlan0 | grep "inet addr:" >> /home/pi/RPi_Temp_Hum_log/network_monitor.log
#ping -c 1 192.168.1.1 | grep '1 received' >> /home/pi/RPi_Temp_Hum_log/network_monitor.log

