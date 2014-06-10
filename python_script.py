from apscheduler.scheduler import Scheduler
from apscheduler import events

#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
import gspread
import logging
import sys
import os

logging.basicConfig(filename='python_script_%d.log' % datetime.datetime.now().weekday(), level=logging.WARNING, format='%(asctime)s %(message)s', filemode='w')

# Start the scheduler
sched = Scheduler(misfire_grace_time = 240)

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
lastPopedTimeStamp = datetime.datetime.now()
lastWdtTimeStamp = datetime.datetime.now()
nofPops = 0
popJobAlias = 0
pushJobAlias1 = 0 
pushJobAlias2 = 0
pushJobAlias3 = 0
pushJobAlias4 = 0
missedPopQueue = 0
popQueueIntervalSeconds=300

def getWorksheet():
    if (os.system("ping -c 4 192.168.1.1") == 0):
        try:
            logging.warning ("getWorksheet: Try login")
            gc = gspread.login(email, password)

        except:
            logging.error ("getWorksheet: Unable to login")
            return 0

        else:
            try:
                logging.warning("getWorksheet: Try open spreadsheet")
                spreadSheet = gc.open(spreadsheetName)

            except:
                logging.error("getWorksheet: Unable to open spread sheet: %s" % spreadsheetName)
                return 0

            else:
                logging.warning("getWorksheet: Open spredsheet succesfully")
                try:
                    workSheet = spreadSheet.get_worksheet(8)
                    
                except:
                    logging.error("getWorksheet: Unable to get worksheet")
                    return 0
                    
                else:
                    return workSheet
    else:
       logging.warning("getWorksheet: No network connection") 
       return 0

def pushQueue ():
    global queueLock
    global pushQueueActive
    
    nofMeas = 10

    if (pushQueueActive == False):
        pushQueueActive = True
        getMoreMeas = True
        validMeasNo = 0
        totalMeasNo = 0
        accTemp = 0
        accHum = 0

        while (getMoreMeas == True):
            #logging.warning ("pushQueue: Measurement no. %d / %d" % (validMeasNo , totalMeasNo))
            #read sensor
            try:
                #logging.warning ("pushQueue: Start subprocess")
                output = subprocess.check_output(["./DHT", "2302", "4"])
                #logging.warning ("pushQueue: End subprocess")

            except:
                logging.warning ("pushQueue: problems execiting subprocess")

            else:
                totalMeasNo = totalMeasNo + 1
                #logging.warning ("pushQueue: Process reading from sensor")
                matchTemp = re.search("Temp =\s+([0-9.]+)", output)
                matchHum = re.search("Hum =\s+([0-9.]+)", output)
       
                if (matchTemp and matchHum):
                    accTemp = accTemp + float(matchTemp.group(1))
                    accHum = accHum + float(matchHum.group(1))
                    logging.warning ("pushQueue: Measurement no. %d; Temp: %.1f; Hum: %.1f " % (validMeasNo , float(matchTemp.group(1)), float(matchHum.group(1))))
                    validMeasNo = validMeasNo + 1

            if (totalMeasNo >= 20):
                getMoreMeas = False
                
            elif (validMeasNo < nofMeas):
                getMoreMeas = True
                time.sleep(15)
                
            else:
                getMoreMeas = False    
        
        while (queueLock == True):
            logging.warning("pushQueue: wait for queueLock")
            time.sleep (2)

        
        dateTimeStamp = datetime.datetime.now()
        queueLock=True
        queueTime.enqueue (dateTimeStamp)
        
        if (validMeasNo > 0):
          tempForLog = accTemp / validMeasNo
          humForLog = accHum / validMeasNo
        else:
          tempForLog = 255 
          humForLog = 255
        
        queueTemperatur.enqueue ("%.1f" % (tempForLog))
        queueHumidity.enqueue ("%.1f" % (humForLog))
          
        queueDebugData.enqueue ("%03d; %02d; %02d" %(queueTime.size(), validMeasNo, totalMeasNo ))          
        queueLock =  False

        logging.warning ("pushQueue: Push sensor reading into Queue - Queue element: %d; Date/time: %s; Temp: %.1f C; Hum: %.1f %%" % (queueTime.size(), dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), tempForLog, humForLog)) 
        pushQueueActive = False  
        reschedulePopQueue(False)
    
    else:
        logging.warning ("pushQueue: Skipped because is already running")

def popQueue ():
    global queueLock
    global popQueueActive
    global pushQueueActive
    global getWorksheetFlag
    global workSheetId
    global lastPopedTimeStamp
    global nofPops

    
  
    if (queueTime.size() != 0 and pushQueueActive == False and popQueueActive == False):
    	#logging.warning ("popQueue: Start")
        popQueueActive = True 
        if (getWorksheetFlag == True):
            popQueueDebugString = '1'
            workSheetId = getWorksheet()
        else:
            popQueueDebugString = '0'

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
                cell_list=workSheetId.range('B2:E2')
                cell_list[0].value=temp
                cell_list[1].value=humidity
                cell_list[2].value=pushDebugData
                cell_list[3].value=datetime.datetime.now().strftime("%H:%M:%S")
                cell_list[3].value+='; %03d; ' %(queueTime.size())
                cell_list[3].value+=popQueueDebugString
                cell_list[3].value+='; %03d' %(nofPops)
                workSheetId.update_cells(cell_list)
                workSheetId.update_cell (2,1,dateTimeStamp)
                
                lastPopedTimeStamp = dateTimeStamp
                
                if (queueTime.size() > 0):
                    reschedulePopQueue(False)
                else:
                    reschedulePopQueue(True)
                    
                nofPops = nofPops + 1
                if (nofPops >=96 and queueTime.size() == 0):
                    logging.warning ("popQueue: Reboot")
                    restart()
      
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
            reschedulePopQueue(True)
            
        popQueueActive = False

    else:
        logging.warning ("popQueue: Skipped. queueSize: %d; pushQueueActive: %d; popQueueActive: %d" %(queueTime.size(), pushQueueActive, popQueueActive))


def wdt():
    global lastPopedTimeStamp
    global lastWdtTimeStamp
    global getWorksheetFlag
   
    
    logging.warning ("wdt: getWorksheetFlag: %d; queueSize: %d; lastWdtTimeStamp: %s, lastPopedTimeStamp: %s" %(getWorksheetFlag, queueTime.size(), lastWdtTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), lastPopedTimeStamp.strftime("%Y-%m-%d %H:%M:%S")))  
    
    if (getWorksheetFlag == False and lastPopedTimeStamp == lastWdtTimeStamp):
    	logging.warning ("wdt: Reset RPi. getWorksheetFlag: %d; queueSize: %d; lastWdtTimeStamp: %s, lastPopedTimeStamp: %s" %(getWorksheetFlag, queueTime.size(), lastWdtTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), lastPopedTimeStamp.strftime("%Y-%m-%d %H:%M:%S")))
    	restart()
    	
    	
    else:
        lastWdtTimeStamp = lastPopedTimeStamp
  

def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)  
    
def reschedulePopQueue (lowFrequency):
    global popQueueIntervalSeconds
    global popJobAlias
    
    if (popJobAlias == 0):
        if (lowFrequency == True):
            popJobAlias = sched.add_interval_job(popQueue, seconds=300)
            popQueueIntervalSeconds = 300
            logging.warning ("First schedule. LowFrequency")
        else:
            popJobAlias = sched.add_interval_job(popQueue, seconds=15)
            popQueueIntervalSeconds = 15
            logging.warning ("First schedule. HighFrequency")
          
    else:
        if (lowFrequency == True):
            if (popQueueIntervalSeconds == 15):
                sched.unschedule_job(popJobAlias)
                popJobAlias = sched.add_interval_job(popQueue, seconds=300)
                popQueueIntervalSeconds = 300
                logging.warning ("Reschedule. LowFrequency")
                
        else:
            if (popQueueIntervalSeconds == 300):
                sched.unschedule_job(popJobAlias)
                popJobAlias = sched.add_interval_job(popQueue, seconds=15)
                popQueueIntervalSeconds = 15
                logging.warning ("Reschedule. HighFrequency")

    
def job_listener(event):
    global missedPopQueue
    global popJobAlias
    global popQueueActive
    global pushQueueActive
    global pushJobAlias1
    global pushJobAlias2
    global pushJobAlias3
    global pushJobAlias4
        
    jobString = "%s" % (event.job)

    if (event.exception):
        if (jobString.find('popQueue') != -1):
            missedPopQueue = missedPopQueue +1
            if (missedPopQueue > 10 ):
                #sched.unschedule_job(popJobAlias)
                missedPopQueue = 0
                popQueueActive = False
                #time.sleep(2)
                #popJobAlias = sched.add_interval_job(popQueue, seconds=15)
                reschedulePopQueue(True)
                logging.warning ("job_listener: popQueue rescheduled")
            else:
                logging.warning ("job_listener: popQueue crashed (%d)" %(missedPopQueue))
        elif (jobString.find('pushQueue') != -1):
            sched.unschedule_job(pushJobAlias1)
            sched.unschedule_job(pushJobAlias2)
            sched.unschedule_job(pushJobAlias3)
            sched.unschedule_job(pushJobAlias4)
            pushQueueActive = False
            time.sleep(2)
            pushJobAlias1=sched.add_cron_job(pushQueue, minute = 10)
            pushJobAlias2=sched.add_cron_job(pushQueue, minute = 25)
            pushJobAlias3=sched.add_cron_job(pushQueue, minute = 40)
            pushJobAlias4=sched.add_cron_job(pushQueue, minute = 55)
            logging.warning ("job_listener: pushQueue rescheduled")
    else:
        if (jobString.find('popQueue') != -1):
            missedPopQueue = 0
            #logging.warning ("job_listener: popQueue sucessful")
        #elif (jobString.find('pushQueue') != -1):
        #    logging.warning ("job_listener: pushQueue sucessful")
        

def main():
    global nofPops
    global popJobAlias
    global pushJobAlias1
    global pushJobAlias2
    global pushJobAlias3
    global pushJobAlias4
      
    nofPops = 0
    #popJobAlias = sched.add_interval_job(popQueue, seconds=15)
    reschedulePopQueue(True)
      
    #sched.add_interval_job(wdt, seconds=1800)

    pushJobAlias1=sched.add_cron_job(pushQueue, minute = 10)
    pushJobAlias2=sched.add_cron_job(pushQueue, minute = 25)
    pushJobAlias3=sched.add_cron_job(pushQueue, minute = 40)
    pushJobAlias4=sched.add_cron_job(pushQueue, minute = 55)
      
    sched.add_listener(job_listener,
           events.EVENT_JOB_EXECUTED |
           events.EVENT_JOB_MISSED |
           events.EVENT_JOB_ERROR)
      
    sched.start()
      
    while True:
        pass

main()
