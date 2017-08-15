import pymonero
import sys
import mysql.connector
import json
import time 


# Initialize daemon (optional unless using different parameters)
#daemon = pymonero.connections.Daemon()
daemon = pymonero.connections.Daemon('http://127.0.0.1','18081')
bitmonero = pymonero.Bitmonero(daemon)

mysqlconfig = {
          'user': 'root',
          'password': '',
          'host': 'localhost',
          'database': 'dimonero',
          'raise_on_warnings': True,
}

def QuotedStr(s):
    return '"%s"'%s

def SingleQuotedStr(s):
    return "'%s'"%s

def dbGetLastHeaderHeight() :

    cnx = mysql.connector.connect(**mysqlconfig)
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = cnx.cursor()

    # get the last header height
    s = "SELECT max(height) FROM header"
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
        print "An Error has occured"
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
        time.sleep(0.01) 
        
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
        time.sleep(0.01) 

def saveAHeaderTxToDB(height):
    #get the data from the node
    data = bitmonero.get_block_by_height(height)
    if hasattr(data,"error"):
        print "An Error has occured"
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
            
            print "Saving txid ", tx_hash, " to the database"
            
            #index increment
            tx_idx = tx_idx + 1

def saveBlockDataToDB():
    #last height in the database
    #dbLastHeight = int(dbGetLastHeaderHeight() or 0)
    
    #do not want to start from the header height. use data from tx instead
    dbLastHeight = int(dbGetLastTxHeight() or 0)
    
    #last height in the monero node
    moneroLastHeight = moneroGetLastHeight()
    #loop until dbLastHeight = moneroLastHeight
    
    #for testing purpose
    #dbLastHeight = 100000
    #moneroLastHeight = 100001
    
    #process the blocks
    while (dbLastHeight < moneroLastHeight):
        #make sure the last height is checked for the completeness of the data
        if dbLastHeight == 0:
            nextHeight = 0
        else:
            nextHeight = dbLastHeight
        #save the header data
        saveAHeaderToDB(nextHeight)
        time.sleep(0.01) 
        saveAHeaderTxToDB(nextHeight)
        time.sleep(0.01) 
        #process the transaction data detail
        txRecords = dbGetTxsBlock(nextHeight)
        i = 0

        for txRecord in txRecords:
            tx_hash = str(txRecord[0])
            tx_idx = int(txRecord[1])
            
            saveATxToDB(nextHeight, tx_idx, tx_hash)
            time.sleep(0.1)
            i = i + 1
        
        #increment
        print "Header with height of ", nextHeight, " has been processed"
        dbLastHeight = nextHeight + 1
        #delay for 0.1 second
        time.sleep(0.01) 
        
#time to update the vout_offset value
def dbUpdateVoutOffsets():
    
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT vout_key, amount FROM tx_vout WHERE vout_offset = -1 ORDER BY header_height ASC, tx_idx ASC, vout_idx ASC"
    
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    #rowcount = len(rows)
    cnx.close()
    hit = 0
    if rowcount > 0 :
        for row in rows:
            vout_key = str(row[0])
            amount = row[1]
            cnx = mysql.connector.connect(**mysqlconfig)
            cur = cnx.cursor()
            s = "SELECT max(vout_offset)+1 FROM tx_vout WHERE amount = %s"
            s = s % (amount)
            cur.execute(s)
            rows = cur.fetchall()
            rowcount = int(cur.rowcount)
            cnx.close()
            #print rows[0]
            newOffset = rows[0][0]

            #update the value
            cnx = mysql.connector.connect(**mysqlconfig)
            cur = cnx.cursor()
            s = "UPDATE tx_vout SET vout_offset = %s WHERE vout_key = %s"
            s = s % (newOffset, QuotedStr(vout_key))
            #print s
            try:
                cur.execute(s)
                cnx.commit()
            except:
                cnx.rollback()
            #close the connection
            cnx.close()
            
            #counter
            hit = hit + 1
            print "vout_key ", vout_key, " has been processed. number ", hit, "of ", rowcount

def dbUpdateAVoutOffset(vout_key):
    
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT amount FROM tx_vout WHERE vout_key = %s"
    s = s % (QuotedStr(vout_key))
    
    cur.execute(s)
    rows = cur.fetchall()
    cnx.close()
    
    for row in rows:
        amount = row[1]
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "SELECT max(vout_offset)+1 FROM tx_vout WHERE amount = %s"
        s = s % (amount)
        cur.execute(s)
        rows = cur.fetchall()
        rowcount = int(cur.rowcount)
        cnx.close()
        newOffset = rows[0][0]

        #update the value
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "UPDATE tx_vout SET vout_offset = %s WHERE vout_key = %s"
        s = s % (newOffset, QuotedStr(vout_key))
        #print s
        try:
            cur.execute(s)
            cnx.commit()
        except:
            cnx.rollback()
        #close the connection
        cnx.close()
        
        #counter
        print "vout_key ", vout_key, " has been processed."


#====================================main program======================================

def main():
    #print "Height in the database: ", dbGetLastHeaderHeight()
    #print "Height in the node: ", moneroGetLastHeight()
    print "start"
    
    #save the block data to database, starting from the last data
    saveBlockDataToDB()
    
    #update the vout_offset data in the database
    #dbUpdateVoutOffsets()
    

    print "finish"
    

if __name__ == "__main__":
    main()

