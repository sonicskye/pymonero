# The script hashes vout_key data of each inputs (k_image) from tx_vin_mixin
# The hash function used is SHA256 from hashlib
# The hashed data format is [vout_key1,vout_key2,vout_key3,...] without square brackets
# The data is then saved to tx_vin_mixin_hash table

import urllib2
import urllib
import json
import mysql.connector
import time 
import csv 
import pymonero
import threading
import hashlib

from utilities import getContent, QuotedStr
from vars import baseUrl, blockUrl, mysqlconfig, monerodUrl, monerodPort

daemon = pymonero.connections.Daemon(monerodUrl,monerodPort)
bitmonero = pymonero.Bitmonero(daemon)

def hashData(rawData):
    h = hashlib.sha256(rawData.encode('utf-8')).hexdigest()
    return h

def mixinOfKimage(k_image):
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT DISTINCT vout_key FROM tx_vin_mixin WHERE k_image = %s"
    s = s % (QuotedStr(k_image))
    #print s
    cur.execute(s)
    rows = cur.fetchall()
    return rows

def mixinOfKimageStr(k_image):
    mixins = mixinOfKimage(k_image)
    #print mixins
    tempStr = ""
    for mixin in mixins:
        print mixin[0]
        if tempStr == "":
            tempStr = mixin[0]
        else:
            tempStr = tempStr + "," + mixin[0]
    return tempStr

def mixinOfKimageCount(k_image):
    mixins = mixinOfKimage(k_image)
    count = 0
    for mixin in mixins:
        count = count + 1
    return count

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
    cur = cnx.cursor()
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

def dbGetLastProcessedHeight():
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT max(header_height) FROM tx_vin_mixin_hash"
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

def hashHeight(height):
    #query key images contained in a block height
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT DISTINCT tx_idx, tx_hash, vin_idx, k_image FROM tx_vin_mixin WHERE header_height = %s"
    s = s % (height)
    cur.execute(s)
    rows = cur.fetchall()
    for row in rows:
        tx_idx = row[0]
        tx_hash = row[1]
        vin_idx = row[2]
        k_image = row[3]
        kimageMixinCount = mixinOfKimageCount(k_image)
        kimageMixinHash = hashData(mixinOfKimageStr(k_image))
        
        #insert data
        s1 = "INSERT INTO tx_vin_mixin_hash (header_height, tx_idx, tx_hash, vin_idx, k_image, vout_key_hash, vout_key_count) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        s1 = s1 % (height, tx_idx, QuotedStr(tx_hash), vin_idx, QuotedStr(k_image), QuotedStr(kimageMixinHash), kimageMixinCount)
        print s1
        cnx1 = mysql.connector.connect(**mysqlconfig)
        cur1 = cnx1.cursor()
        try:
            cur1.execute(s)
            cnx1.commit()
        except:
            cnx1.rollback()
        #close the connection
        cnx1.close()
        
         
    #close the connection
    cnx.close()
    return height

#prepare for threading
class myThread (threading.Thread):
    #query key images contained in a block height
    def __init__(self, threadID, name, height):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.height = height
    def run(self):      
        hashHeight(self.height)
      
#the controller to run the thread from the last processed block to the latest data available
def runHashHeight(threadSize):
    
    #firstHeight = dbGetLastProcessedHeight()
    firstHeight = 110
    #lastHeight = dbGetLastTxHeight() 
    lastHeight = 114
    print "First block: ", str(firstHeight)
    print "Last BLock: ", str(lastHeight)
    
    while (firstHeight <= lastHeight):
        #make sure the last height is checked for the completeness of the data
        if firstHeight == 0:
            nextHeight = 0
        else:
            nextHeight = firstHeight
            
        #thread
        threads = []
        for i in range(1,threadSize):
            if firstHeight < lastHeight:
                # Create new threads
                thread = myThread(i, "Thread-"+str(i), nextHeight)
                # Start new Threads
                thread.start()
                # Add threads to thread list
                threads.append(thread)
                #increase the height
                nextHeight = nextHeight + 1
                firstHeight = nextHeight
        # Wait for all threads to complete
        for t in threads:
            t.join()

def main():
    #use xxxx threads at once
    #saveAllToDB(1)
    runHashHeight(2)


if __name__ == "__main__":
    main()