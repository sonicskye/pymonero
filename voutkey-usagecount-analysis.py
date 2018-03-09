# The script analyses the voutkey_usagecount data
# It works by creating a query to aggregate the usage per n blocks
# The data is then saved or published as a diagram

import urllib2
import urllib
import json
import mysql.connector
import time 
import csv 
import pymonero
import threading
import matplotlib.pyplot as plt 

from utilities import getContent, QuotedStr
from vars import baseUrl, blockUrl, mysqlconfig, monerodUrl, monerodPort

daemon = pymonero.connections.Daemon(monerodUrl,monerodPort)
bitmonero = pymonero.Bitmonero(daemon)

def moneroGetLastHeight():
    last_block_header = bitmonero.get_last_block_header()
    lastHeight = -1
    if hasattr(last_block_header,"error"):
       print "reply error" 
    else:
        jsonResponse = json.loads(last_block_header.to_JSON())
        lastHeight = jsonResponse["height"]
        return lastHeight

def dbGetLastTxHeight():

    cnx = mysql.connector.connect(**mysqlconfig)
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = cnx.cursor()

    # get the last header height
    s = "SELECT max(header_height) FROM tx_vin_mixin"
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    height = -1
    if rowcount > 0 :
        for row in rows:
            height = row[0]
            if (str(height) == "None"):
                height = 0
    #close the connection
    cnx.close()
    return height

def dbGetFinalTxHeight():
    cnx = mysql.connector.connect(**mysqlconfig)
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = cnx.cursor()

    # get the last header height
    s = "SELECT max(header_height) FROM header_tx"
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    height = -1
    if rowcount > 0 :
        for row in rows:
            height = row[0]
            if (str(height) == "None"):
                height = 0
    #close the connection
    cnx.close()
    return height

#prepare for threading
class myThread (threading.Thread):
   def __init__(self, threadID, name, height):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.height = height
   def run(self):      
      saveAHeaderToDB(self.height)
      print "Header with height of ", self.height, " has been processed"

def saveAllToDB(threadSize):
    #fixing things
    lastBlock = dbGetLastTxHeight()
    firstBlock = lastBlock - 200
    #lastBlock = dbGetFinalTxHeight()
    print "First block: ", str(firstBlock)
    print "Last BLock: ", str(lastBlock)
    #firstBlock = 1014786
    #lastBlock = 1014787
    height = firstBlock
    #make sure that the blocks are already permanent
    while height < (lastBlock-10):
        #thread
        threads = []
        for i in range(1,threadSize):
            if height < (lastBlock-10):
                # Create new threads
                thread = myThread(i, "Thread-"+str(i), height)
                # Start new Threads
                thread.start()
                # Add threads to thread list
                threads.append(thread)
                height = height + 1
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
def saveAHeaderToDB(height):
    s = "INSERT INTO voutkey_usagecount(vout_key, usagecount) SELECT m.vout_key, count(m.vout_key) AS usagecountnew FROM tx_vin_mixin m WHERE m.header_height = %s GROUP BY m.vout_key ON DUPLICATE KEY UPDATE usagecount = VALUES(usagecount)"
    s = s % (height)
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    try:
        cur.execute(s)
        cnx.commit()
    except:
        cnx.rollback()
    #close the connection
    cnx.close()
    
def createQryVoutkeyUsageSum(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, SUM(u.usagecount) as sumusage FROM tx_vout v, voutkey_usagecount u WHERE v.vout_key = u.vout_key AND v.header_height BETWEEN %s and %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, SUM(u.usagecount) as sumusage FROM tx_vout v, voutkey_usagecount u WHERE v.vout_key = u.vout_key AND v.header_height BETWEEN %s and %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def createQryVoutkeyCount(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, COUNT(v.vout_key) as voutkeycount FROM tx_vout v WHERE v.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, COUNT(v.vout_key) as voutkeycount FROM tx_vout v WHERE v.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def createQryTxCount(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, COUNT(h.tx_idx) as txcount FROM header_tx h WHERE h.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, COUNT(h.tx_idx) as txcount FROM header_tx h WHERE h.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def createQryMixinCount(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, COUNT(m.vout_key) as mixincount FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, COUNT(m.vout_key) as mixincount FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def createQryMixinAge(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, SUM(m.header_height - m.vout_header_height) as headerdiff FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, SUM(m.header_height - m.vout_header_height) as headerdiff FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def createQryMixinHeaderAvg(blockInterval, maxHeight):
    s = ""
    #maxHeight = dbGetFinalTxHeight()
    numX = maxHeight // blockInterval # integer division to get the number of UNION we need to create
    remainder = maxHeight % blockInterval # remainder
    for i in range(0,numX):
        sTemp = ""
        localMin = i * blockInterval
        localMax = localMin + blockInterval
        sTemp = "SELECT %s as height, AVG(m.vout_header_height) as headeravg FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (localMax, localMin, localMax - 1)
        if i == 0:
            # the beginning of the select
            s = sTemp
        else:
            # after the first SELECT then we need UNIONs
            s = s + " UNION ( %s )"
            s = s % (sTemp)
    # set up the remainder
    if (numX > 0) and (remainder > 0):
        sTemp = "SELECT %s as height, AVG(m.vout_header_height) as headeravg FROM tx_vin_mixin m WHERE m.header_height BETWEEN %s AND %s"
        sTemp = sTemp % (numX * blockInterval + remainder, numX * blockInterval, numX * blockInterval + remainder - 1)
        s = s + " UNION ( %s )"
        s = s % (sTemp)
        
    return s

def showQry(qry):
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = qry
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    height = -1
    if rowcount > 0 :
        for row in rows:
            print row[0], row[1]
    #close the connection
    cnx.close()
    
def plotQry(qry):
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = qry
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    height = -1
    aHeight = []
    aUsage = []
    if rowcount > 0 :
        for row in rows:
            aHeight.append(row[0])
            aUsage.append(row[1])
    #close the connection
    cnx.close()
    plt.plot(aUsage, aHeight)
    plt.savefig(test1.png)

def main():
    #use xxxx threads at once
    #while True:
    #    saveAllToDB(5)
    #    time.sleep(600)
    #print createQryVoutkeyUsageSum(10000,dbGetFinalTxHeight())
    #print createQryVoutkeyUsageSum(10000,1517798)
    
    #print createQryVoutkeyUsageSum(5000,1517709)
    #print createQryVoutkeyCount(1000,1517709)
    #print createQryTxCount(1000,1517709)
    #print createQryMixinCount(1000,1517709)
    #print createQryMixinAge(1000,1517709)
    #showQry(createQry(100000))
    print createQryMixinHeaderAvg(10000,1517709)

if __name__ == "__main__":
    main()