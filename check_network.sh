NOW=$(date +"%D-%H:%M:%S") 
if  ping -c 4 192.168.1.1  >/dev/null ; then
    echo $NOW  "Network connection up!" >> /home/pi/RPi_Temp_Hum_log/check_network.log
    
#else
#    echo $NOW  "Network connection down!" >> /home/pi/RPi_Temp_Hum_log/check_network.log
fi
