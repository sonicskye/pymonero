#!/bin/env python2.7

import pymonero
import sys
import mysql.connector
import json
import time
import csv 

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
            
            try:
                cur.execute(s)
                cnx.commit()
            except:
                cnx.rollback()
            #close the connection
            cnx.close()
            
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
            headerVin = "INSERT INTO tx_vin (header_height, tx_idx, tx_hash, amount, k_image, key_offsets, vin_idx) VALUES "
            dataVin = ""
            for vin in vins:
                singleVin = ""
                amount = vin["key"]["amount"]
                k_image = vin["key"]["k_image"]
                key_offsets = vin["key"]["key_offsets"]
                
                singleVin = "(%s, %s, %s, %s, %s, %s, %s)"
                singleVin = singleVin % (header_height, tx_idx, QuotedStr(tx_hash), amount, QuotedStr(k_image), QuotedStr(key_offsets), idx)
                #print singleVin
                if dataVin =="":
                    dataVin = singleVin
                else:
                    dataVin = str(dataVin) + "," + str(singleVin)
                
                #increase vin index
                idx = idx + 1
            #print dataVin
            if dataVin <> "":
                s = headerVin + dataVin
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
                time.sleep(0.01) 
            
            #print s    
            #process the vout
            #since we only have a single transaction, therefore we only process the index 0
            vouts = jsonResponse2["found"][0]["vout"]
            headerVout = "INSERT INTO tx_vout (header_height, tx_idx, amount, vout_key, tx_hash, vout_idx, vout_offset) VALUES "
            dataVout = ""
            
            idx = 0
            #for temporary, set the vout_offset to 0
            vout_offset = -1
            for vout in vouts:
                singleVout = ""
                amount = vout["amount"]
                vout_key = vout["target"]["key"]
                
                singleVout = "(%s, %s,%s, %s, %s, %s, %s)"
                singleVout = singleVout % (header_height, tx_idx, amount, QuotedStr(vout_key), QuotedStr(tx_hash), idx, vout_offset)
                if dataVout =="":
                    dataVout = singleVout
                else:
                    dataVout = str(dataVout) + "," + str(singleVout)
                
                #increase vin index
                idx = idx + 1
            
            #send to the database
            if dataVout <> "":
                s = headerVout + dataVout
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
                time.sleep(0.01) 
            #print s    
            #print "Saving txid ", tx_hash, " details to the database"
            

def saveBlockDataToDB():
    #last height in the database
    #dbLastHeight = int(dbGetLastHeaderHeight() or 0)
    
    #do not want to start from the header height. use data from tx instead
    dbLastHeight = int(dbGetLastTxHeight() or 0)
    
    #last height in the monero node
    moneroLastHeight = moneroGetLastHeight()

    #for testing purpose
    dbLastHeight = 121606
    moneroLastHeight = 121607
    
    #process the blocks
    #loop until dbLastHeight = moneroLastHeight
    #while (dbLastHeight < (moneroLastHeight - 10)):
    while (dbLastHeight < (moneroLastHeight)):
        #make sure the last height is checked for the completeness of the data
        if dbLastHeight == 0:
            nextHeight = 0
        else:
            nextHeight = dbLastHeight
        #save the header data
        saveAHeaderToDB(nextHeight)
        time.sleep(0.001) 
        saveAHeaderTxToDB(nextHeight)
        time.sleep(0.001) 
        #increment
        print "Header with height of ", nextHeight, " has been processed"
        dbLastHeight = nextHeight + 1
        #delay for 0.1 second
        #time.sleep(0.001) 

def saveBlockDataFromCSV(fileName):
    with open(fileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            blockHeight = int(row[0])
            saveAHeaderToDB(blockHeight)
            time.sleep(0.001) 
            saveAHeaderTxToDB(blockHeight)
            time.sleep(0.001) 
            #increment
            print "Header with height of ", blockHeight, " has been processed"

    
#====================================main program======================================

def main():
    #print "Height in the database: ", dbGetLastHeaderHeight()
    #print "Height in the node: ", moneroGetLastHeight()
    print "start"
    
    #save the block data to database, starting from the last data
    #saveBlockDataToDB()
    
    #using bulk queries!!!!!!!!!!!!!!!!!!!!!!!!
    saveBlockDataFromCSV('blocklist.csv')
    
    #print dbGetTxsBlock(81352)
    #txRecords = dbGetTxsBlock(81352)
    #i = 0

    #for txRecord in txRecords:
    #    tx_hash = str(txRecord[0])
    #    print tx_hash
    #    tx_idx = int(txRecord[1])
        
        #saveATxToDB(nextHeight, tx_idx, tx_hash)
        #time.sleep(0.01)
    #    i = i + 1
    
    #update the vout_offset data in the database
    #dbUpdateVoutOffsets()
    

    print "finish"
    

if __name__ == "__main__":
    main()

