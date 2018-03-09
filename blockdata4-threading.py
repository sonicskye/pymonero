#!/bin/env python2.7

import pymonero
import sys
import mysql.connector
import json
import time 
import csv 
import threading

from utilities import QuotedStr, SingleQuotedStr
from vars import mysqlconfig, monerodUrl, monerodPort

# Initialize daemon (optional unless using different parameters)
#daemon = pymonero.connections.Daemon()
daemon = pymonero.connections.Daemon(monerodUrl,monerodPort)
bitmonero = pymonero.Bitmonero(daemon)

def dbGetLastHeaderHeight() :

    cnx = mysql.connector.connect(**mysqlconfig)
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = cnx.cursor()

    # get the last header height
    s = "SELECT max(height) FROM header"
    #s = "SELECT max(header_height) FROM header_tx"
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

def dbGetLastTxHeight() :

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
    #close the connection
    cnx.close()
    return height

def moneroGetLastHeight():
    last_block_header = bitmonero.get_last_block_header()
    lastHeight = -1
    if hasattr(last_block_header,"error"):
       print "reply error" 
    else:
        jsonResponse = json.loads(last_block_header.to_JSON())
        lastHeight = jsonResponse["height"]
        return lastHeight
    
def saveAHeaderToDB(height):
    #get the data from the node
    data = bitmonero.get_block_header_by_height(height)
    if hasattr(data,"error"):
        print "An Error in the header data has occured. Block height: " + str(height)
    else:
        #put the result to variables
        jsonResponse = json.loads(data.to_JSON())
        #print data.to_JSON()
        hash = jsonResponse["hash"]
        height = jsonResponse["height"]
        difficulty = jsonResponse["difficulty"]
        major_version = jsonResponse["major_version"]
        minor_version = jsonResponse["minor_version"]
        nonce = jsonResponse["nonce"]
        prev_hash = jsonResponse["prev_hash"]
        reward = jsonResponse["reward"]
        timestamp = jsonResponse["timestamp"]
        
        #save to database
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "INSERT INTO header (hash, height, difficulty, major_version, minor_version, nonce, prev_hash, reward, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        s = s % (QuotedStr(hash), height, difficulty, major_version, minor_version, nonce, QuotedStr(prev_hash), reward, timestamp)
        
        #print s
        try:
            cur.execute(s)
            cnx.commit()
        except:
            cnx.rollback()
        
        #close the connection
        cnx.close()
    #print "Header with height of ", height, " has been processed"
        
#get tx list of a block
def dbGetTxsBlock(height):
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()

    # get the transactions data from the database
    s = "SELECT tx_hash, tx_idx FROM header_tx WHERE header_height = %s ORDER BY tx_idx ASC"
    s = s % (height)
    
    cur.execute(s)
    results = cur.fetchall()
    #close the connection
    cnx.close()
    return results


#save a single transaction to database
def saveATxToDB(header_height, tx_idx, tx_hash):
    #get the data from the node
    #tx_hash = SingleQuotedStr(tx_hash)
    data = bitmonero.get_transactions(tx_hash)
    #print data
    jsonResponse = json.loads(data.to_JSON())
    #print jsonResponse
    
    #process the vin
    #since we only have a single transaction
    vins = jsonResponse["found"][0]["vin"]
    #print vins
    idx = 0
    for vin in vins:
        amount = vin["key"]["amount"]
        k_image = vin["key"]["k_image"]
        key_offsets = vin["key"]["key_offsets"]
        
        #save to database
        #this is where the error comes from#######################
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "INSERT INTO tx_vin (header_height, tx_idx, tx_hash, amount, k_image, key_offsets, vin_idx) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        s = s % (header_height, tx_idx, QuotedStr(tx_hash), amount, QuotedStr(k_image), QuotedStr(key_offsets), idx)
        
        try:
            cur.execute(s)
            cnx.commit()
        except:
            cnx.rollback()
        #close the connection
        cnx.close()
        
        #increase vin index
        idx = idx + 1
        #time.sleep(0.01) 
        
    #process the vout
    #since we only have a single transaction, therefore we only process the index 0
    vouts = jsonResponse["found"][0]["vout"]
    
    idx = 0
    #for temporary, set the vout_offset to 0
    vout_offset = -1
    for vout in vouts:
        amount = vout["amount"]
        vout_key = vout["target"]["key"]
        
        #save to database
        #this is where the error comes from#######################
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "INSERT INTO tx_vout (header_height, tx_idx, amount, vout_key, tx_hash, vout_idx, vout_offset) VALUES (%s, %s,%s, %s, %s, %s, %s)"
        s = s % (header_height, tx_idx, amount, QuotedStr(vout_key), QuotedStr(tx_hash), idx, vout_offset)
        
        try:
            cur.execute(s)
            cnx.commit()
        except:
            cnx.rollback()
        #close the connection
        cnx.close()
        
        #increase vin index
        idx = idx + 1
        #time.sleep(0.01) 
    print "Saving txid ", tx_hash, " details to the database"

def saveAHeaderTxToDB(height):
    #get the data from the node
    data = bitmonero.get_block_by_height(height)
    if hasattr(data,"error"):
        print "An Error has occured when retrieving the tx data of block number " + str(height)
    else:
        #put the result to variables
        jsonResponse = json.loads(data.to_JSON())
        #print data.to_JSON()
        header_hash = jsonResponse["header"]["hash"]
        header_height = jsonResponse["header"]["height"]
        tx_hashes = jsonResponse["details"]["tx_hashes"]
        
        #save the block reward
        vouts = jsonResponse["details"]["miner_tx"]["vout"]
        vout_idx = 0
        #for temporary, set the vout_offset to 0 #TODO calculate the vout_offset based on the amount index
        vout_offset = -1
        for vout in vouts:
            vout_amount = vout["amount"]
            vout_key = vout["target"]["key"]
            #save to database
            cnx = mysql.connector.connect(**mysqlconfig)
            cur = cnx.cursor()
            s = "INSERT INTO tx_vout (header_height, tx_idx, amount, vout_key, tx_hash, vout_idx, vout_offset) VALUES (%s, %s,%s, %s, %s, %s, %s)"
            s = s % (height, -1, vout_amount, QuotedStr(vout_key), QuotedStr("reward"), vout_idx, vout_offset)
            #print s
            try:
                cur.execute(s)
                cnx.commit()
            except:
                cnx.rollback()
            #close the connection
            cnx.close()
            time.sleep(0.1) 
            
            #increase vin index
            vout_idx = vout_idx + 1
                  
        #save the tx hashes
        tx_idx = 0
        for tx_hash in tx_hashes:
            #save to database
            cnx = mysql.connector.connect(**mysqlconfig)
            cur = cnx.cursor()
            s = "INSERT INTO header_tx (tx_hash, tx_idx, header_height, header_hash) VALUES (%s, %s, %s, %s)"
            s = s % (QuotedStr(tx_hash), tx_idx, QuotedStr(header_height), QuotedStr(header_hash))
            
            try:
                cur.execute(s)
                cnx.commit()
            except:
                cnx.rollback()
            #close the connection
            cnx.close()
            time.sleep(0.1) 
            
            #print "Saving txid ", tx_hash, " to the database"
            
            #index increment
            tx_idx = tx_idx + 1
            
            ##########################save the tx detail here, trial#################################
            xid = str(tx_hash)
            data2 = bitmonero.get_transactions(xid)
            jsonResponse2 = json.loads(data2.to_JSON())
            
            #process the vin
            #since we only have a single transaction
            vins = jsonResponse2["found"][0]["vin"]
            idx = 0
            for vin in vins:
                singleVin = ""
                amount = vin["key"]["amount"]
                k_image = vin["key"]["k_image"]
                key_offsets = vin["key"]["key_offsets"]
                #there are tx with large key offsets, we are removing this data for convenience
                key_offsets = ""
                
                s = "INSERT INTO tx_vin (header_height, tx_idx, tx_hash, amount, k_image, key_offsets, vin_idx) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                s = s % (header_height, tx_idx, QuotedStr(tx_hash), amount, QuotedStr(k_image), QuotedStr(key_offsets), idx)
                #print s
                #send the vin to the database
                cnx = mysql.connector.connect(**mysqlconfig)
                cur = cnx.cursor()
                
                try:
                    cur.execute(s)
                    cnx.commit()
                except:
                    cnx.rollback()
                #close the connection
                cnx.close()
                time.sleep(0.1) 
                
                #increase vin index
                idx = idx + 1
                 
            #process the vout
            #since we only have a single transaction, therefore we only process the index 0
            vouts = jsonResponse2["found"][0]["vout"]
            
            idx = 0
            #for temporary, set the vout_offset to 0
            vout_offset = -1
            for vout in vouts:
                singleVout = ""
                amount = vout["amount"]
                vout_key = vout["target"]["key"]
                
                s = "INSERT INTO tx_vout (header_height, tx_idx, amount, vout_key, tx_hash, vout_idx, vout_offset) VALUES (%s, %s,%s, %s, %s, %s, %s)"
                s = s % (header_height, tx_idx, amount, QuotedStr(vout_key), QuotedStr(tx_hash), idx, vout_offset)
                #print s
                cnx = mysql.connector.connect(**mysqlconfig)
                cur = cnx.cursor()
                
                try:
                    cur.execute(s)
                    cnx.commit()
                except:
                    cnx.rollback()
                #close the connection
                cnx.close()
                time.sleep(0.1) 
                #increase vin index
                idx = idx + 1
             
            #print "Saving txid ", tx_hash, " details to the database"
    #print "    Tx Data of block", height, "has been processed" 
    
#prepare for threading
class myThread (threading.Thread):
   def __init__(self, threadID, name, height):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.height = height
   def run(self):      
      saveAHeaderToDB(self.height)
      saveAHeaderTxToDB(self.height)
      print "Header with height of ", self.height, " has been processed"
      
      

def saveBlockDataToDB(threadSize):
    #last height in the database
    #dbLastHeight = int(dbGetLastHeaderHeight() or 0)
    
    #do not want to start from the header height. use data from tx instead
    dbLastHeight = int(dbGetLastTxHeight() or 0)
    
    #last height in the monero node
    moneroLastHeight = moneroGetLastHeight()
    
    #process the blocks
    #loop until dbLastHeight = moneroLastHeight
    #while (dbLastHeight < (moneroLastHeight - 10)):
    while (dbLastHeight <= (moneroLastHeight - 10)):
        #make sure the last height is checked for the completeness of the data
        if dbLastHeight == 0:
            nextHeight = 0
        else:
            nextHeight = dbLastHeight
            
        #thread
        threads = []
        for i in range(1,threadSize):
            if dbLastHeight < (moneroLastHeight - 10):
                # Create new threads
                thread = myThread(i, "Thread-"+str(i), nextHeight)
                # Start new Threads
                thread.start()
                # Add threads to thread list
                threads.append(thread)
                #increase the height
                nextHeight = nextHeight + 1
                dbLastHeight = nextHeight
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
def saveBlockDataFromCSV(fileName):
    with open(fileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            blockHeight = int(row[0])
            saveAHeaderToDB(blockHeight)
            #time.sleep(0.001) 
            saveAHeaderTxToDB(blockHeight)
            #time.sleep(0.001) 
            #increment
            print "Header with height of ", blockHeight, " has been processed"


#====================================main program======================================

def main():
    print "Height in the database: ", dbGetLastHeaderHeight()
    print "Height in the node: ", moneroGetLastHeight()
    print "start"
    
    #save the block data to database, starting from the last data
    saveBlockDataToDB(10)
    
    #using single queries!!!!!!!!!!!!!!!!!!!!!!!!
    #saveBlockDataFromCSV('blocklist.csv')
    
    

    print "finish"
    

if __name__ == "__main__":
    main()

