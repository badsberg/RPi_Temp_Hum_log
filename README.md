RPi_Temp_Hum_log
================

Python script for logging Temperatur and Humidity using a DHT22/AM2302 sensor

- Brænd Raspbian image (findes her: http://www.raspberrypi.org/). Brug Win32 Disk Imager til at brænde image (http://sourceforge.net/projects/win32diskimager/)
- Brug raspi-config til at configurere
- Opsæt WIFI. (følg denne vejledning : http://pingbin.com/2012/12/setup-wifi-raspberry-pi/)
- Installer GIT ('sudo apt-get install git-core'eller http://quick2wire.com/articles/a-gentle-guide-to-git-and-github/) 
- Installer gspread ('wget http://pypi.python.org/packages/source/g/gspread/gspread-0.0.15.tar.gz'; tar -zxvf gspread-0.0.15.tar.gz; sudo python setup.py install)
- Install BCM2835 C (look for latest version here http://www.airspayce.com/mikem/bcm2835/index.html) 
- Install RPi (git clone https://github.com/badsberg/RPi_Temp_Hum_log.git)
- Compile DHT.C (gcc DHT.c -l bcm2835 -std=gnu99 -o DHT)
- Installer Apscheduler (wget https://pypi.python.org/packages/source/A/APScheduler/APScheduler-2.1.0.tar.gz; sudo tar -xzvf APScheduler-2.1.0.tar.gz; python setup.py install)
- Lav så python scriptet starter automatisk (følg denne vejledning: http://elinux.org/RPi_Debian_Auto_Login; hvor der skal benyttes 'sudo /home/pi/)
