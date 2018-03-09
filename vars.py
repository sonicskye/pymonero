monerodUrl = 'http://127.0.0.1'
monerodPort = '18081'

onionPort = "8081"
onionServerUrl = monerodUrl + ":" + onionPort
baseUrl = onionServerUrl + "/api/transaction/"
blockUrl = onionServerUrl + "/api/block/"

mysqlconfig = {
          'user': 'root',
          'password': '',
          'host': 'localhost',
          'database': 'monero',
          'raise_on_warnings': True,
}
