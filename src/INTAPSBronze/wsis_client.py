# File Desc: Contains the definition of class that is used to connect with WSIS
#
# Program Author: Rediet Worku aka Aethiops II ben Zahab
#
# Date Created: 22nd of Septemeber 2024, Monday
import http.client
import json
import datetime
from datetime import datetime

class WSISClient:
    """
    Connect's with WSIS Server/RESTful API and post's payment bills
    """
    def __init__(self):
        self.sessionID = ""
        self.conn = None
        self.state = False
        self.paymentCenter = {}         # wsis payment center info
        self.username = ""              # wsis username

        self.headers = {
            'content-type':'application/json',
            'connection':'keep-alive'
        }


    def connect(self, host, port):
        """
        Start's a TCP connection with WSIS Server

        :param host: hostname or ip address
        :param port: the port # for WSIS Server
        """
        self.conn = http.client.HTTPConnection(host, port)
        self.state = True


    def disconnect(self):
        """
        Tear's down the active connection with WSIS
        """
        if self.state:
            self.conn.close()

        self.state = False


    def startSession(self, uname, password):
        """
        After successful TCP connection, we need to start application level session with
        WSIS Server and get it's session ID, this is done by requesting the API with
        the right credentials

        :param uname: username for the payment center
        :param password: pwd for payment center
        """
        if self.state == False:
            return
        
        pars = {
            "UserName":uname,
            "Password":password,
            "Source":"Bronze"
        }
        self.conn.request('POST', '/api/app/server/CreateUserSession', headers=self.headers, body=json.dumps(pars))
        res = self.conn.getresponse()
        result = json.loads(res.read().decode('utf-8'))
        
        if res.status == 200:
            self.sessionID = result
            self.username = uname
            return True
        
        return False
    

    def getPaymentCenter(self):
        """
        initalizes paymentCenter member object by using the info from WSIS Server itself, 
        rather than acquiring it from db
        """
        if self.state == False or self.sessionID == "":
            return
        
        pars = {
            "sessionID": self.sessionID,
            "userID": self.username
        }
        self.conn.request('POST', '/api/erp/subscribermanagment/GetPaymentCenter', headers=self.headers, body=json.dumps(pars))
        res = self.conn.getresponse()
        self.paymentCenter = json.dumps(res.read().decode('utf-8'))
        

    def postBillPayment(self, rawPayments, iqe, instrumentCode, assetID, town):
        """
        For each payments made from INSA Derash, this function post's the payments to WSIS
        
        :param payments: A listof payments made through INSA Derash
        :param iqe: An object of DB interface
        :param instrumentCode: Cash Code or Instrument code (WSIS stuff)
        :param assetID: WSIS asset account ID
        :param town: the utility town name
        """
        payments = rawPayments.split('\n')[1:]
        
        for payment in payments:
            pay = payment.split(',')
            if town in pay[3]:
                pay[3] = pay[3].split('-')[1]
            bills = iqe.getSettledBills(pay[3].strip('"'))

            if len(pay) < 8:
                print(pay)
                continue
            obj = {
                "sessionID": self.sessionID,
                "receipt": {
                "receiptNumber":None,
                "offline":True,
                "mobile":False,
                "notifyCustomer":False,
                "settledBills": bills,
                "assetAccountID": assetID, #3345,
                "tranTicks": self.dateToTicks(datetime.now()),
                "paymentInstruments": [{
                "depositToBankAccountID": -1,
                "instrumentTypeItemCode": instrumentCode,
                "bankBranchID": None,
                "accountNumber": None,
                "documentReference": None,
                "documentDate": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "remark":None,
                "amount": float(pay[4])
                }],
                "bankDepositDocuments": [],
                "customer": None,
                "customerID": -1,
                "billBatchID": -1,
                "summarizeTransaction": False,
                "offlineBills": None,
                "AccountDocumetnID": -1,
                "documentTypeID": -1,
                "paperRef": "",
                "shortDescription": f"Settled through Derash. Confirmation code: {pay[-1]}, Agent: {pay[-2]}",
                "longDescription": None,
                "reversed": False,
                "scheduled": False,
                "materialized": False,
                "materializedOn": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "totalAmount": -1.0,
                "totalInstrument": float(pay[-4]),
                "isFutureDate": False,
                "documentDate": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "posted": False
                }
            }
            print(pay)
            print(json.dumps(obj))
            break


    def dateToTicks(self, date):
        """
        Convert's the date format to C# style of Ticks
        
        :param datetime: the date in question
        :return: long int of date as milisecond ticks
        """
        result = (date - datetime(1,1,1)).total_seconds() * 10**7
        return f"{result:17.0f}"