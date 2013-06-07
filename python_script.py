from apscheduler.scheduler import Scheduler

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

logging.basicConfig(filename='python_script.log',level=logging.WARNING, format='%(asctime)s %(message)s')


# Start the scheduler
sched = Scheduler()

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
nofFailedLogin = 0
nofFailedOpenWorksheet = 0
nofFailedGetWorksheet = 0
nofFailedRunSubprocess = 0
nofFailedUpdateCell = 0
popQueueDebugString = ''

def getWorksheet():
    global nofFailedLogin
    global nofFailedOpenWorksheet
    global nofFailedGetWorksheet
    global popQueueDebugString
    
    if (os.system("ping -c 1 192.168.1.1") == 0):
        try:
            logging.warning ("getWorksheet: Try login")
            gc = gspread.login(email, password)

        except:
            nofFailedLogin =+ 1
            logging.error ("getWorksheet: Unable to login")
            return 0

        else:
            popQueueDebugString = '%d / ' %(nofFailedLogin)
            nofFailedLogin = 0
            
            try:
                logging.warning("getWorksheet: Try open spreadsheet")
                spreadSheet = gc.open(spreadsheetName)

            except:
                nofFailedOpenWorksheet =+ 1
                logging.error("getWorksheet: Unable to open spread sheet: %s" % spreadsheetName)
                return 0

            else:
                popQueueDebugString += '%d / ' %(nofFailedOpenWorksheet)
                nofFailedOpenWorksheet = 0
                logging.warning("getWorksheet: Open spredsheet succesfully")
                try:
                    workSheet = spreadSheet.get_worksheet(7)
                    
                except:
                    nofFailedGetWorksheet += 1
                    logging.error("getWorksheet: Unable to get worksheet")
                    return 0
                    
                else:
                    popQueueDebugString += '%d / ' %(nofFailedGetWorksheet)
                    nofFailedGetWorksheet = 0
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
            logging.warning ("pushQueue: Measurement no. %d / %d" % (validMeasNo , totalMeasNo))
            #read sensor
            try:
                logging.warning ("pushQueue: Start subprocess")
                output = subprocess.check_output(["./DHT", "2302", "4"])
                logging.warning ("pushQueue: End subprocess")

            except:
                loging.warning ("pushQueue: problems execiting subprocess")

            else:
                totalMeasNo = totalMeasNo + 1
                logging.warning ("pushQueue: Process reading from sensor")
                matchTemp = re.search("Temp =\s+([0-9.]+)", output)
                matchHum = re.search("Hum =\s+([0-9.]+)", output)
       
                if (matchTemp and matchHum):
                    accTemp = accTemp + float(matchTemp.group(1))
                    accHum = accHum + float(matchHum.group(1))
                    validMeasNo = validMeasNo + 1

            if (totalMeasNo >= 20):
                getMoreMeas = False
                
            elif (validMeasNo < nofMeas):
                getMoreMeas = True
                time.sleep(30)
                
            else:
                getMoreMeas = False    
        
        while (queueLock == True):
            logging.warning("pushQueue: wait for queueLock")
            time.sleep (2)

        dateTimeStamp = datetime.datetime.now()
        queueLock=True
        queueTime.enqueue (dateTimeStamp)
        queueTemperatur.enqueue ("%.1f" % (accTemp / validMeasNo))
        queueHumidity.enqueue ("%.1f" % (accHum / validMeasNo))
        queueDebugData.enqueue (" %d / %d / %d" %(queueTime.size(), validMeasNo, totalMeasNo ))
        queueLock =  False

        logging.warning ("pushQueue: Push sensor reading into Queue - Queue element: %d; Date/time: %s; Temp: %.1f C; Hum: %.1f %%" % (queueTime.size(), dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), accTemp / nofMeas, accHum / nofMeas)) 
        pushQueueActive = False  
    
    else:
        logging.warning ("pushQueue: Skipped because is already running")

def popQueue ():
    global queueLock
    global popQueueActive
    global pushQueueActive
    global nofFailedUpdateCell
    global popQueueDebugString

    logging.warning ("popQueue: Start")
  
    if (queueTime.size() != 0 and pushQueueActive == False and popQueueActive == False):
        popQueueActive = True   
        workSheet = getWorksheet()
        if (workSheet != 0):
            while (queueLock == True):
            	logging.warning("popQueue: wait for queueLock")
            	time.sleep (2)
      
        queueLock = True
        queueSize = queueTime.size()
        dateTimeStamp = queueTime.dequeue()
        temp = queueTemperatur.dequeue()
        humidity = queueHumidity.dequeue()
        debugData = queueDebugData.dequeue()
        queueLock = False
        
        logging.warning ("popQueue: Pop sensor reading from Queue - Queue element: %d; Date/time: %s; Temp: %s C; Hum: %s  %%" % (queueSize, dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), temp, humidity))
        try:
            #cell_list=worksheet.range('A2:C2')
            #cell_list[0].value=dateTimeStamp
            #cell_list[1].value=temp
            #cell_list[2].value=humidity
            #workSheet.update_cells(cell_list)
            workSheet.update_cell (2,1,dateTimeStamp)
            workSheet.update_cell (2,2,temp)
            workSheet.update_cell (2,3,humidity)
            workSheet.update_cell (2,4,debugData)
            popQueueDebugString += '%d' %(nofFailedUpdateCell)
            print (popQueueDebugString)
            nofFailedUpdateCell = 0
            workSheet.update_cell (2,5,datetime.datetime.now().strftime("%H:%M:%S / %s "%(popQueueDebugString)))

        except:
            nofFailedUpdateCell += 1
            queueLock = True
            queueTime.enqueue (dateTimeStamp)
            queueTemperatur.enqueue (temp)
            queueHumidity.enqueue (humidity)
            queueDebugData.enqueue (debugData)
            queueLock = False
            logging.warning ("popQueue: Did not write measurement at time %s into spreadsheet."  % dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"))
          
        popQueueActive = False
    else:
        logging.warning ("popQueue: Skipped. queueSize: %d; pushQueueActive: %d; popQueueActive: %d" %(queueTime.size(), pushQueueActive, popQueueActive))
        logging.warning ("popQueue: End")

def main():
      #pushQueue()
      #popQueue()

      sched.add_interval_job(popQueue, seconds=60)

      sched.add_cron_job(pushQueue, minute =  0)
      sched.add_cron_job(pushQueue, minute = 15)
      sched.add_cron_job(pushQueue, minute = 30)
      sched.add_cron_job(pushQueue, minute = 45)

      #sched.add_cron_job(pushQueue, minute =  5)
      #sched.add_cron_job(pushQueue, minute = 20)
      #sched.add_cron_job(pushQueue, minute = 35)
      #sched.add_cron_job(pushQueue, minute = 50)

      #sched.add_cron_job(pushQueue, minute = 10)
      #sched.add_cron_job(pushQueue, minute = 25)
      #sched.add_cron_job(pushQueue, minute = 40)
      #sched.add_cron_job(pushQueue, minute = 55)

      sched.start()
      
      while True:
        pass

main()
