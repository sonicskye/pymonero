import pymonero
import sys
import mysql.connector
import json
import time 
import blockdata

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
    time.sleep(0.01)
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
            time.sleep(0.01)
            
def main():
    print "Height in the database: ", blockdata.dbGetLastHeaderHeight()
    #print "Height in the node: ", blockdata.moneroGetLastHeight()
    
    #save the block data to database, starting from the last data
    #saveBlockDataToDB()
    
    #update the vout_offset data in the database
    dbUpdateVoutOffsets()
    

    print "finish"
    

if __name__ == "__main__":
    main()