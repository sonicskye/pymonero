import pymonero
import sys
import json

# Initialize daemon (optional unless using different parameters)
#daemon = pymonero.connections.Daemon()
#daemon = pymonero.connections.Daemon('http://127.0.0.1','38081')
daemon = pymonero.connections.Daemon('http://127.0.0.1','18081')
bitmonero = pymonero.Bitmonero(daemon)

txid = "9c3c0086ef9aa98f370dac303c5dca109678bf95c9e4252e103dab16dce46fa8"
txid2 = "eb6dbe1925c50ef87e0d0d01fe0457d42a227f734d36f41722e494e1f2f3052b"
transactions = bitmonero.get_transactions(txid)
transactions2 = bitmonero.get_transactions(txid2)
transactions3 = bitmonero.get_block_by_height(1236637)

#transactions = bitmonero.get_block_by_height(100000)
#transactions = bitmonero.get_block_header_by_height(0)
jsonResponse = json.loads(transactions.to_JSON())
print jsonResponse

jsonResponse2 = json.loads(transactions2.to_JSON())
print jsonResponse2

jsonResponse3 = json.loads(transactions3.to_JSON())
print jsonResponse3


#if hasattr(transactions,"error"):
#    print(transactions.error)
#else:
#    print(transactions.to_JSON())
#    
#if hasattr(transactions2,"error"):
#    print(transactions2.error)
#else:
#    print(transactions2.to_JSON())

#transactions = bitmonero.get_block_header_by_height(1000)
#if hasattr(transactions,"error"):
#    print(transactions.error)
#else:
#    print(transactions.to_JSON())