import urllib2
import urllib
import json
import mysql.connector
import time 
import csv 

from utilities import getContent, QuotedStr
from vars import baseUrl, mysqlconfig

def dbGetLastTxHeight():

    cnx = mysql.connector.connect(**mysqlconfig)
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = cnx.cursor()

    # get the last header height
    s = "SELECT max(header_height) FROM tx_vin_mixin where header_height >= 400000 and header_height < 500000"
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
        print "key image: ", k_image , "(amount: " , amount , ")"
        mixins = input["mixins"]
        for mixin in mixins:
            public_key = mixin["public_key"]
            block_no = mixin["block_no"]
            print "-   public key: ", public_key, " (" , block_no , ")"

def saveTxDetailToDB():
    firstBlock = dbGetLastTxHeight()
    lastBlock = dbGetFinalTxHeight()
    #firstBlock = 400000
    #lastBlock = 500000
    print "First block: ", str(firstBlock)
    print "Last BLock: ", str(lastBlock)
    #firstBlock = 1014786
    #lastBlock = 1014787
    height = firstBlock
    while height < lastBlock:
        #get tx_hash
        s = "SELECT tx_hash, tx_idx FROM header_tx WHERE header_height = %s ORDER BY tx_idx ASC"
        s = s % (height)
        
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        cur.execute(s)
        results = cur.fetchall()
        #close the connection
        cnx.close()
        
        
        for result in results:
            tx_hash = result[0]
            tx_idx = result[1]
            #print baseUrl + tx_hash
            data = getContent(baseUrl + tx_hash)
            #print data
            jsonResponse = json.loads(data)
            #print jsonResponse
            inputs = jsonResponse["data"]["inputs"]
            #print inputs
            vin_idx = 0
            for input in inputs:
                amount = input["amount"]
                k_image = input["key_image"]
                #print "key image: ", k_image , "(amount: " , amount , ")"
                mixins = input["mixins"]
                mixin_idx = 0
                
                for mixin in mixins:
                    public_key = mixin["public_key"]
                    block_no = mixin["block_no"]
                    #print "-   public key: ", public_key, " (" , block_no , ")"
                    headerVinMixin = "INSERT INTO tx_vin_mixin (header_height, k_image, tx_hash, tx_idx, vin_idx, mixin_idx, vout_header_height, vout_key) VALUES "
                    dataVinMixin = "(%s, %s, %s, %s, %s, %s, %s, %s)"
                    dataVinMixin = dataVinMixin % (height, QuotedStr(k_image), QuotedStr(tx_hash), tx_idx, vin_idx, mixin_idx, block_no, QuotedStr(public_key))
                    
                    s = ""
                    s = headerVinMixin + dataVinMixin
                    cnx = mysql.connector.connect(**mysqlconfig)
                    cur = cnx.cursor()
                    try:
                        cur.execute(s)
                        cnx.commit()
                    except:
                        cnx.rollback()
                    #close the connection
                    cnx.close()
                    #print s
                    time.sleep(0.01)
                    
                    #increment
                    mixin_idx = mixin_idx + 1
                
                #increment
                vin_idx = vin_idx + 1

        print "Block height " + str(height) + " processed."
        #increment
        height = height + 1
        
def saveAHeaderToDB(height):
    #get tx_hash
    s = "SELECT tx_hash, tx_idx FROM header_tx WHERE header_height = %s ORDER BY tx_idx ASC"
    s = s % (height)
    
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    cur.execute(s)
    results = cur.fetchall()
    #close the connection
    cnx.close()
    
    
    for result in results:
        tx_hash = result[0]
        tx_idx = result[1]
        #print baseUrl + tx_hash
        data = getContent(baseUrl + tx_hash)
        #print data
        jsonResponse = json.loads(data)
        #print jsonResponse
        inputs = jsonResponse["data"]["inputs"]
        #print inputs
        vin_idx = 0
        for input in inputs:
            amount = input["amount"]
            k_image = input["key_image"]
            #print "key image: ", k_image , "(amount: " , amount , ")"
            mixins = input["mixins"]
            mixin_idx = 0
            
            for mixin in mixins:
                public_key = mixin["public_key"]
                block_no = mixin["block_no"]
                #print "-   public key: ", public_key, " (" , block_no , ")"
                headerVinMixin = "INSERT INTO tx_vin_mixin (header_height, k_image, tx_hash, tx_idx, vin_idx, mixin_idx, vout_header_height, vout_key) VALUES "
                dataVinMixin = ""
                dataVinMixin = "(%s, %s, %s, %s, %s, %s, %s, %s)"
                dataVinMixin = dataVinMixin % (height, QuotedStr(k_image), QuotedStr(tx_hash), tx_idx, vin_idx, mixin_idx, block_no, QuotedStr(public_key))
                    
                s = headerVinMixin + dataVinMixin
                cnx = mysql.connector.connect(**mysqlconfig)
                cur = cnx.cursor()
                try:
                    cur.execute(s)
                    cnx.commit()
                except:
                    cnx.rollback()
                #close the connection
                cnx.close()
                #print s
                time.sleep(0.01) 
                
                #increment
                mixin_idx = mixin_idx + 1
            
            #increment
            vin_idx = vin_idx + 1
            
        
def saveBlockDataFromCSV(fileName):
    with open(fileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            blockHeight = int(row[0])
            saveAHeaderToDB(blockHeight)
            time.sleep(0.001) 
            #increment
            print "Header with height of ", blockHeight, " has been processed"

def main():
    #getTxData("eb8a8d2e5b36643e34ebab993d76c510747013e368d6233f20278cd92d64c2b0")
    saveTxDetailToDB()
    #saveBlockDataFromCSV('blocklistmixin.csv')
    #getContent("https://xmrchain.net/api/transaction/023f327c998fe73358a71bcc5e0c7ee69944cc5b897d48b17c7c808524bb0cab")
    #getContent("https://moneroexplorer.com/api/transaction/023f327c998fe73358a71bcc5e0c7ee69944cc5b897d48b17c7c808524bb0cab")


if __name__ == "__main__":
    main()