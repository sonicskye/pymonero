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

#this should not be used
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

#this should not be used
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

#unused
def getTxData(tx_hash):
    data = getContent(baseUrl + tx_hash)
    #print data
    jsonResponse = json.loads(data)
    #print jsonResponse["data"]["inputs"]
    inputs = jsonResponse["data"]["inputs"]
    #print inputs
    for input in inputs:
        amount = input["amount"]
        k_image = input["key_image"]
        #print "key image: ", k_image , "(amount: " , amount , ")"
        mixins = input["mixins"]
        for mixin in mixins:
            public_key = mixin["public_key"]
            block_no = mixin["block_no"]
            #print "-   public key: ", public_key, " (" , block_no , ")"
            
#prepare for threading
class myThreadHeader (threading.Thread):
   def __init__(self, threadID, name, height):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.height = height
   def run(self):      
      saveAHeaderToDB(self.height)

def saveAllToDB(threadSize):
    #fixing things
    #firstBlock = dbGetLastTxHeight()
    #start from the first block
    firstBlock = 0
    lastBlock = moneroGetLastHeight()
    #lastBlock = dbGetFinalTxHeight()
    print "First block: ", str(firstBlock)
    print "Last BLock: ", str(lastBlock)
    #firstBlock = 1014786
    #lastBlock = 1014787
    height = firstBlock
    #make sure that the blocks are already permanent
    while height <= (lastBlock-10):
        #thread
        threads = []
        for i in range(1,threadSize):
            if height < (lastBlock-10):
                # Create new threads
                thread = myThreadHeader(i, "Thread-"+str(i), height)
                # Start new Threads
                thread.start()
                # Add threads to thread list
                threads.append(thread)
                height = height + 1
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
def saveAHeaderToDB(height):
    #data from onion
    blockData = getContent(blockUrl + str(height))
    blockJsonResponse = json.loads(blockData)
    txs = blockJsonResponse["data"]["txs"]
     
    for tx in txs:
        #saveTxDetailToDB(tx)
        isCoinbase = tx["coinbase"]
        if not isCoinbase:
            tx_hash = tx["tx_hash"]
            saveTxDetailToDB(str(tx_hash))
        
        
    print "Block height " + str(height) + " processed."
    #increment
    height = height + 1
        
def saveTxDetailToDB(tx_hash):
    #print baseUrl + tx_hash
    data = getContent(baseUrl + tx_hash)
    #print data
    jsonResponse = json.loads(data)
    #print jsonResponse
    inputs = jsonResponse["data"]["inputs"]
    outputs = jsonResponse["data"]["outputs"]
    #set tx_idx = 0 because we do not have the data in the onion explorer
    tx_idx = 0
    #print inputs
    vin_count = 0
    for input in inputs:
        #increment
        vin_count = vin_count + 1
    
    vout_count = 0
    for output in outputs:
        #increment
        vout_count = vout_count + 1
        
    s = "INSERT INTO tx_io (tx_hash, numinputs, numoutputs) VALUES (%s, %s, %s)"
    s = s % (QuotedStr(tx_hash), vin_count, vout_count)
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    try:
        cur.execute(s)
        cnx.commit()
    except:
        cnx.rollback()
    #close the connection
    cnx.close()
    
def fixMissingHeader(threadSize):
    #set up query where headers are not found compared to a control table
    #count the number first
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "select count(distinct m.header_height) from tx_vin_mixin m where not exists (select i.tx_hash from tx_io i where i.tx_hash = m.tx_hash);"
    cur.execute(s)
    results = cur.fetchone()
    cnx.close()
    if results is not None:
        num = int(results[0])
    else:
        num = 0
    print "Total data to fix: ", num
    #now get the value
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "select distinct m.header_height from tx_vin_mixin m where not exists (select i.tx_hash from tx_io i where i.tx_hash = m.tx_hash);"
    
    cur.execute(s)
    heights = cur.fetchall()
    cnx.close()
    
    counter = 0
    for i in range(0,num):
        threads = []
        for j in range(0,threadSize):
            if counter <= num:
                # Create new threads
                thread = myThreadHeader(i, "Thread-"+str(i), heights[counter][0])
                # Start new Threads
                thread.start()
                # Add threads to thread list
                threads.append(thread)
                counter = counter + 1
        #Wait for all threads to complete
        for t in threads:
            t.join()

def main():
    #use xxxx threads at once
    #saveAllToDB(1)
    fixMissingHeader(10)


if __name__ == "__main__":
    main()