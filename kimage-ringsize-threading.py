#the script will compute ring size of each key image.
#the raw data is taken from tx_vin_mixin table.

import urllib2
import urllib
import json
import mysql.connector
import time 
import csv 
import pymonero
import threading

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
    firstBlock = lastBlock - 500
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
    s = "INSERT INTO kimage_ringsize(k_image, ringsize) SELECT m.k_image, count(m.vout_key) AS ctx FROM tx_vin_mixin m WHERE m.header_height = %s GROUP BY m.k_image ON DUPLICATE KEY UPDATE ringsize = VALUES(ctx)"
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

def main():
    #use xxxx threads at once
    while True:
        saveAllToDB(5)
        time.sleep(600)


if __name__ == "__main__":
    main()