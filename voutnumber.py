import pymonero
import sys
import mysql.connector
import json
import time 
import blockdata
import datetime

daemon = pymonero.connections.Daemon('http://127.0.0.1','18081')
bitmonero = pymonero.Bitmonero(daemon)

mysqlconfig = {
          'user': 'root',
          'password': '',
          'host': '127.0.0.1',
          'database': 'dimonero',
          'raise_on_warnings': True,
}

def QuotedStr(s):
    return '"%s"'%s

def SingleQuotedStr(s):
    return "'%s'"%s

def dbGetLastBlock():
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT MAX(header_height) FROM tx_vout WHERE vout_num > -1"
    cur.execute(s)
    rows = cur.fetchall()
    for row in rows:
        height = row[0]
    return height

def dbGetMaxBlock():
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT MAX(header_height) FROM tx_vout WHERE vout_num = -1"
    cur.execute(s)
    rows = cur.fetchall()
    for row in rows:
        height = row[0]
    return height
            
def dbUpdateBlockVoutNum(height):
    #take the current time
    startTime = datetime.datetime.now()
    
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT vout_key, amount FROM tx_vout WHERE header_height = %s ORDER BY tx_idx ASC, vout_idx ASC"
    s = s % (height)
    print s
    cur.execute(s)
    rows = cur.fetchall()
    rowcount = int(cur.rowcount)
    #rowcount = len(rows)
    cnx.close()
    #time.sleep(0.1)
    hit = 0
    for row in rows:
        vout_key = str(row[0])
        amount = row[1]
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "SELECT max(vout_offset)+1 FROM tx_vout WHERE amount = %s"
        s = s % (amount)
        print s
        cur.execute(s)
        rows2 = cur.fetchall()
        rowcount2 = int(cur.rowcount)
        cnx.close()
        #print rows[0]
        newOffset = rows2[0][0]
        if str(newOffset) == "None":
            newOffset = 0

        #update the value
        cnx = mysql.connector.connect(**mysqlconfig)
        cur = cnx.cursor()
        s = "UPDATE tx_vout SET vout_offset = %s WHERE vout_key = %s"
        s = s % (newOffset, QuotedStr(vout_key))
        print s
        try:
            cur.execute(s)
            cnx.commit()
        except:
            cnx.rollback()
        #close the connection
        cnx.close()
        
        #counter
        hit = hit + 1
        
        time.sleep(0.1)
    
    #take the current time
    finishTime = datetime.datetime.now()
    #calculate the difference
    timeDiff = finishTime - startTime
    
    #notification
    print "vout_key of block ", height, " has been processed. time: ", str(timeDiff)
            
def main():

    
    cnx = mysql.connector.connect(**mysqlconfig)
    cur = cnx.cursor()
    s = "SELECT max(vout_offset)+1 FROM tx_vout WHERE amount = 10000000000001"
    cur.execute(s)
    rows2 = cur.fetchall()
    rowcount2 = int(cur.rowcount)
    cnx.close()
    #print rows[0]
    newOffset = rows2[0][0]
    if str(newOffset) == "None":
        newOffset = 0
    print newOffset

if __name__ == "__main__":
    main()