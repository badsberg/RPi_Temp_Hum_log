from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler import events
from oauth2client.client import SignedJwtAssertionCredentials

#from apscheduler.events import *

#!/usr/bin/python

import json
import subprocess
import re
import sys
import time
import datetime
import gspread
import logging
import sys
import os



#logging.basicConfig(filename='python_script_%d.log' % datetime.datetime.now().weekday(), level=logging.ERROR, format='%(asctime)s %(message)s', filemode='w')
#logging.basicConfig(filename='python_script_%d.log' % datetime.datetime.now().weekday(), level=logging.WARNING, format='%(asctime)s %(message)s')

# Start the scheduler
sched = BackgroundScheduler()

# ===========================================================================
# Google Account Details
# ===========================================================================

# Account details for google docs
email       = sys.argv[1]
password    = sys.argv[2]
spreadsheetName = 'TempFugtLog'





# ===========================================================================
# Example Code
# ===========================================================================

class Queue:
  def __init__(self):
    self.items = []

  def isEmpty(self):
    return self.items == []
  
  def enqueue(self, item):
    self.items.insert(0,item)
	
  def dequeue(self):
    return self.items.pop()
	
  def size(self):
    return len(self.items)

queueTime = Queue()
queueTemperatur = Queue()
queueHumidity = Queue()
queueDebugData = Queue()
queueLock = False
pushQueueActive = False
popQueueActive = False
getWorksheetFlag = True
workSheetId = 0
nofPops = 0
popJobAlias = 0
nofMissedPops = 0
summarySheet = 0
inputSheet = 0
credentials = 0;

def getWorksheet():
    global inputSheet
    global summarySheet	
    global credentials

    if (os.system("ping -c 4 www.google.com") == 0):
        try:
            #logging.warning ("getWorksheet: Try login")
            gc = gspread.authorize(credentials)
            #gc = gspread.login(email, password)

        except:
            logging.error ("getWorksheet: Unable to login. email: %s; password: %s" % (email,password))
            return 0

        else:
            time.sleep(5)
            try:
                #logging.warning("getWorksheet: Try open spreadsheet")
                spreadSheet = gc.open(spreadsheetName)

            except:
                logging.error("getWorksheet: Unable to open spread sheet: %s" % spreadsheetName)
                return 0

            else:
            	time.sleep(5)
                #logging.warning("getWorksheet: Open spredsheet succesfully")
                try:
                    inputSheet = spreadSheet.get_worksheet(8)
                    summarySheet = spreadSheet.get_worksheet(0)
                    
                except:
                    logging.error("getWorksheet: Unable to get worksheet")
                    return 0
                    
                else:
                    return 1
    else:
       logging.warning("getWorksheet: No network connection") 
       return 0

def pushQueue ():
    global queueLock
    global pushQueueActive
    
    temp=[]
    hum=[]
    
    nofMeas = 7

    if (pushQueueActive == False):
        pushQueueActive = True
        getMoreMeas = True
        validMeasNo = 0
        totalMeasNo = 0
        accTemp = 0
        accHum = 0

        while (getMoreMeas == True):
            #logging.warning ("pushQueue: Measurement no. %d / %d" % (validMeasNo , totalMeasNo))
            try:
                #output = "Temp = 20.0, Hum = 50.0, Retry = 5\n" 
                output = subprocess.check_output(["./DHT1", "2302", "4"])
 
            except:
                logging.warning ("pushQueue: problems execiting subprocess")

            else:
                totalMeasNo = totalMeasNo + 1
                #logging.warning ("pushQueue: Sensor output :%s", output)
                matchTemp = re.search("Temp =\s+(-?[0-9.]+)", output)
                matchHum = re.search("Hum =\s+([0-9.]+)", output)
                matchRetry = re.search("Retry =\s+([0-9]+)", output)
       
                if (matchTemp and matchHum):
                    #accTemp = accTemp + float(matchTemp.group(1))
                    #accHum = accHum + float(matchHum.group(1))
                    temp.append(float(matchTemp.group(1)))
                    hum.append(float(matchHum.group(1)))
                    logging.warning ("pushQueue: Measurement no. %d; Temp: %.1f; Hum: %.1f; Retry: %d " % (validMeasNo , float(matchTemp.group(1)), float(matchHum.group(1)), int(matchRetry.group(1))))
                    validMeasNo = validMeasNo + 1

            if (totalMeasNo >= 30):
                getMoreMeas = False
                
            elif (validMeasNo < nofMeas):
                getMoreMeas = True
                time.sleep(5)
                
            else:
                getMoreMeas = False    
        
        while (queueLock == True):
            logging.warning("pushQueue: wait for queueLock")
            time.sleep (2)
            
        temp.sort()
        hum.sort()
        print("pushQueue: Temp meas: ", temp[0:len(temp)])
        print("pushQueue: Hum meas: " ,  hum[0:len(hum)])
        
        
        nofAvgMeas = 0; 
        for x in range(0, validMeasNo - 4):
		accTemp = accTemp + temp.pop(2)
		accHum =  accHum + hum.pop(2)
		nofAvgMeas = nofAvgMeas + 1 
        
        dateTimeStamp = datetime.datetime.now()
        queueLock=True
        queueTime.enqueue (dateTimeStamp)
        
        
        if (nofAvgMeas > 0):
		tempForLog = accTemp / nofAvgMeas
		humForLog = accHum / nofAvgMeas
	else:
		logging.warning ("pushQueue: Sensor not working. Reboot")
		#restart()
		time.sleep (10)
        
        queueTemperatur.enqueue ("%.1f" % (tempForLog))
        queueHumidity.enqueue ("%.1f" % (humForLog))
          
        queueDebugData.enqueue ("%03d; %02d; %02d" %(queueTime.size(), nofAvgMeas, totalMeasNo ))          
        queueLock =  False

        logging.warning ("pushQueue: Push sensor reading into Queue - Queue element: %d; Date/time: %s; Temp: %.1f C; Hum: %.1f %%" % (queueTime.size(), dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), tempForLog, humForLog)) 
        pushQueueActive = False  
        reschedulePopQueue(True)
    
    else:
        logging.warning ("pushQueue: Skipped because is already running")

def popQueue ():
    global queueLock
    global popQueueActive
    global pushQueueActive
    global getWorksheetFlag
    global workSheetId
    global nofPops
    global nofMissedPops
    global inputSheet
    global summarySheet	
    
    logging.warning ("popQueue: Start")
    
    if (queueTime.size() != 0 and pushQueueActive == False and popQueueActive == False):
        popQueueActive = True 
        if (getWorksheetFlag == True):
            workSheetId = getWorksheet()

        if (workSheetId != 0):
            getWorksheetFlag = False
            while (queueLock == True):
            	logging.warning("popQueue: wait for queueLock")
            	time.sleep (2)
      
            queueLock = True
            queueSize = queueTime.size()
            dateTimeStamp = queueTime.dequeue()
            temp = queueTemperatur.dequeue()
            humidity = queueHumidity.dequeue()
            pushDebugData = queueDebugData.dequeue()
            queueLock = False
        
            
            logging.warning ("popQueue: Pop sensor reading from Queue - Queue element: %d; Date/time: %s; Temp: %s C; Hum: %s  %%" % (queueSize, dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), temp, humidity))
            try:
                cell_list=inputSheet.range('A2:E2')
                cell_list[0].value=dateTimeStamp
                cell_list[1].value=temp
                cell_list[2].value=humidity
                cell_list[3].value=pushDebugData
                cell_list[4].value=datetime.datetime.now().strftime("%H:%M:%S")
                cell_list[4].value+='; %03d; ' %(queueTime.size())
                cell_list[4].value+='%01d' %(nofMissedPops)
                cell_list[4].value+='; %03d' %(nofPops)

                #logging.warning ("popQueue: Reset nofMissedPops (%d)" %(nofMissedPops))
                nofMissedPops = 0
                
                inputSheet.update_cells(cell_list)
                summarySheet.update_cell (35,12,datetime.datetime.now())
                
                if (queueTime.size() <= 0):
                    reschedulePopQueue(False)
                    
                nofPops = nofPops + 1
                if (nofPops >=96 and queueTime.size() == 0):
                    logging.warning ("popQueue: Reboot")
                    restart()
                #if (nofPops >=999)
                #	nofPops = 0
      
            except:
                getWorksheetFlag = True
                queueLock = True
                queueTime.enqueue (dateTimeStamp)
                queueTemperatur.enqueue (temp)
                queueHumidity.enqueue (humidity)
                queueDebugData.enqueue (pushDebugData)
                queueLock = False
                logging.warning ("popQueue: Did not write measurement at time %s into spreadsheet."  % dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"))

            else:
                try:
            	    summarySheet.update_cell (35,12,datetime.datetime.now())
            	    
            	except:
		    logging.warning ("popQueue: Did not write pop time into spreadsheet." )
            	 	
    	    
    	else:
            reschedulePopQueue(False)
            
        popQueueActive = False

    else:
        logging.warning ("popQueue: Skipped. queueSize: %d; pushQueueActive: %d; popQueueActive: %d" %(queueTime.size(), pushQueueActive, popQueueActive))
   
    logging.warning ("popQueue: End")
    
def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)  
    
def reschedulePopQueue (restartJob):
    global popJobAlias
    global popQueueActive
    
    if (popJobAlias == 0):
        if (restartJob == True):
            popJobAlias = sched.add_job(popQueue, 'interval', seconds=70)
            #logging.warning ("reschedulePopQueue: First schedule.")

    else:
    	popQueueActive =  False
        if (restartJob == False):
            popJobAlias.remove()
            popJobAlias = 0
            #logging.warning ("reschedulePopQueue: Stop schedule")
                
        else:
            popJobAlias.remove()
            time.sleep (2)
            popJobAlias = sched.add_job(popQueue, 'interval', seconds=70)
            #logging.warning ("reschedulePopQueue: Restart.")

    
def job_listener(event):
    global nofMissedPops
    
    nofMissedPops = nofMissedPops + 1
    logging.warning ("job_listener: Exception. nofMissedPops %d" %(nofMissedPops))
    
    if nofMissedPops > 8:
    	reschedulePopQueue(True)
      

def main():
	global credentials
	
	sched.add_job(pushQueue, 'cron', minute = 00)
	sched.add_job(pushQueue, 'cron', minute = 15)
	sched.add_job(pushQueue, 'cron', minute = 30)
	sched.add_job(pushQueue, 'cron', minute = 45)
      
	sched.add_listener(job_listener,events.EVENT_JOB_MISSED)
      
	sched.start()
    
	json_key = json.load(open('TempFugt-a227d45db1ab.json'))
	scope = ['https://spreadsheets.google.com/feeds']
	credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
      
	while True:
		#pass
		time.sleep(30)

main()
