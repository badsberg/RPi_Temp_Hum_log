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

logging.basicConfig(filename='python_script.log',level=logging.WARNING, format='%(asctime)s %(message)s')


# Start the scheduler
sched = Scheduler(coalesce = True)

# ===========================================================================
# Google Account Details
# ===========================================================================

# Account details for google docs
email       = sys.argv[0]
password    = sys.argv[1]
spreadsheetName = 'TempFugtLog'
print ("email '%s'; password '%s'" %(email, password))

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
queueLock = False
pushQueueActive = False
popQueueActive = False

def getWorksheet():
  try:
    gc = gspread.login(email, password)

  except:
    logging.error ("Unable to login")
    return 0

  else:
    try:
      spreadSheet = gc.open(spreadsheetName)

    except:
      logging.error("Unable to open spread sheet: %s" % spreadsheetName)
      return 0

    else:
      workSheet = spreadSheet.get_worksheet(7)
      return workSheet
     


def pushQueue ():
  global queueLock
  global pushQueueActive
  accTemp = 0
  accHum = 0
  nofMeas = 10

  pushQueueActive = True
  getMoreMeas = True
  measNo = 0

  while (getMoreMeas == True):
    logging.warning ("pushQueue: Measurement no. %d" % measNo)
    #read sensor
    try:
      logging.warning ("pushQueue: Start subprocess")
      output = subprocess.check_output(["./Adafruit_DHT", "2302", "4"])
      logging.warning ("pushQueue: End subprocess")

    except:
      loging.warning ("pushQueue: problems execiting subprocess")

    else:
      logging.warning ("pushQueue: Process reading from sensor")
      matchTemp = re.search("Temp =\s+([0-9.]+)", output)
      matchHum = re.search("Hum =\s+([0-9.]+)", output)
       
      if (matchTemp and matchHum):
        #print("counter: %d; Temp: %.1f; hum: %.1f" % (measNo, float(matchTemp.group(1)), float(matchHum.group(1))))
        accTemp = accTemp + float(matchTemp.group(1))
        accHum = accHum + float(matchHum.group(1))
        measNo = measNo +1

    if (measNo < nofMeas):
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
  queueTemperatur.enqueue ("%.1f" % (accTemp / nofMeas))
  queueHumidity.enqueue ("%.1f" % (accHum / nofMeas))
  queueLock =  False

  logging.warning ("pushQueue: Push sensor reading into Queue - Queue element: %d; Date/time: %s; Temp: %.1f C; Hum: %.1f %%" % (queueTime.size(), dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), accTemp / nofMeas, accHum / nofMeas)) 
  pushQueueActive = False  

def popQueue ():
  global queueLock
  global popQueueActive
  global pushQueueActive

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
      queueLock = False
        
      logging.warning ("popQueue: Pop sensor reading from Queue - Queue element: %d; Date/time: %s; Temp: %s C; Hum: %s  %%" % (queueSize, dateTimeStamp.strftime("%Y-%m-%d %H:%M:%S"), temp, humidity))
      try:
        #cell_list=worksheet.range('A2:C2')
        #cell_list[0].value=dateTimeStamp
        #cell_list[1].value=temp
        #cell_list[2].value=humidity
        #workSheet.update_cells(cell_list)
        workSheet.update_cell (2,9,queueTime.size())
        workSheet.update_cell (2,1,dateTimeStamp);
        workSheet.update_cell (2,2,temp);
        workSheet.update_cell (2,3,humidity);

      except:
        queueLock = True
        queueTime.enqueue (dateTimeStamp)
        queueTemperatur.enqueue (temp)
        queueHumidity.enqueue (humidity)
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
