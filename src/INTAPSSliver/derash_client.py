# File Desc: A client app that connects to Derash router owned by INSA (Information Network Security Agency)
#   owned by the federal government of Ethiopia. The purpose of this module is to sync water bill payments
#   between water supply utilites/enterprsies and Derash that acts as a middle-man between various banks.
#   The aim is to utilize the power of internet for online electronic payments.
#
# Program Author: Rediet Worku aka Aethiops II ben Zahab
#
# Date Created: 21st of Septemeber 2024, Saturday
import http.client
import json
from datetime import datetime



class DerashClient:
    """
    Orgranizes all the functions we need to exchange information with Derash
    """
    def __init__(self, domain, apiKey, apiSecret, town, port=http.client.HTTPS_PORT):
        """
        Read's Derash connection parameters from app.config file (JSON format)
        and starts an https connection with Derash

        :param domain: the host domain address to connect to
        :param apiKey: the apiKey provided from INSA Derash
        :param apiSecret: the Secret key that is paired with apiKey
        :param town: the town for the utility
        :param port: the https port default 443
        """
        self.domain = domain
        self.port = port
        self.conn = None
        self.town = town
        self.state = False      # a connection state

        self.headers = {
            'content-type':'application/json',
            'api-key':f'{apiKey}',
            'api-secret':f'{apiSecret}',
            'connection':'keep-alive',
        }
    

    def connect(self):
        """
        Start's HTTPS connection with derash router and returns it's connection 
        """
        self.conn = http.client.HTTPSConnection(self.domain, self.port)
        self.state = True
    
    
    def disconnect(self):
        """
        Tear's down the active connection
        """
        if self.state:
            self.conn.close()

        self.state = False


    def uploadDerash(self, iqe):
        """
        Reterives a list of unpaid bills from the database, and foreach bill found it 
        checks derash router for the bill info, updates bill changes if any, finally uploads
        bills to derash

        :param iqe: an instance of database engine, uses it to query the database for bill info
        """
        # get a list-of-all the unpaid bills
        bills = iqe.getUnpaidBills()
        period = iqe.getCurrentPeriod()

        print(f"Uploading {len(bills)} bills to Derash API.")

        for bill in bills:
            derashBill = self.getBillDerash(bill)
            print(derashBill)
            if len(derashBill) != 0:
                self.updateDerash(bill, derashBill)
                continue

            self.uploadNewDerash(bill, period)

    
    def updateDerash(self, sysBill, derashBill):
        """
        A previously uploaded bill if not already paid maybe updated from the Utility System
        which is WSIS, in such cases the bill needs to be updated accordingly using the 
        provided API from INSA Derash (see derash docs for list of API's).
        
        :param sysBill: the bill info to update
        :param derashBill: the bill from derash to comapre to and update
        """
        if sysBill["customerCode"] == derashBill["customer_id"] or sysBill["contractNo"] == derashBill["customer_id"]:
            if round(sysBill["amount"], 2) - round(derashBill["amount_due"], 2) >= 0.1:
                updateBill = {
                    "bill_id":derashBill["bill_id"],
                    "bill_desc":derashBill["bill_desc"],
                    "reason":"Updated from utility system",
                    "already_paid":False,
                    "amount_due":sysBill["amount"],
                    "due_date":derashBill["due_date"]
                }
                self.conn.request('PUT', '/biller/customer-bill-data', body=json.dump(updateBill))
                res = self.conn.getresponse()
                res.read().decode('utf-8')  # discard
    

    def getBillDerash(self, bill):
        """
        Get's the bill info provided by parameter bill from INSA Derash API.
        
        :param bill: the bill info to reterive
        :return: empty object if bill does not exist on derash
        """
        billID = self.town + str(bill["billID"])
        self.conn.request('GET', f"/biller/customer-bill-data?bill_id={billID}", headers=self.headers)
        res = self.conn.getresponse()
        result = json.loads(res.read().decode('utf-8'))

        if res.status == 200:
            return result
        else: # we don't really care about other codes...
            return {}
        

    def uploadNewDerash(self, bill, period):
        """
        Upload's the newly generated or not synced bills to INSA Derash. Since function is run
        after checking if bill exists in INSA Derash DB, we are sure this bill does not exist
        
        :param bill: the new bill data to upload to derash
        :param period: the current bill period
        """
        uploadBill = {
            "bill_id": self.town + str(bill.billID),
            "bill_desc": "bills upto " + period,
            "reason": "bills upto " + period,
            "amount_due": round(bill["amount"], 2),
            "due_date": datetime().today().strftime("%Y-%m-%d"),
            "partial_pay_allowed": False,
            "customer_id": bill["customerCode"],
            "name": bill["name"],
            "mobile": bill["phoneNo"],
            "email": bill["email"]
        }
        self.conn.request('POST', "/biller/customer-bill-data", headers=self.headers, body=json.dumps(uploadBill))
        res = self.conn.getresponse()
        print(res.read().decode('utf-8'))


    def invalidateBill(self, iqe):
        """
        Removes/deactivates all deleted bills by WSIS users to INSA Derash domain. The trick is to look
        into *_Deleted tables and if corresponding id is found in INSA Derash and remove it!

        :param iqe: an object of db interface, used to run qryUnpaidBillsDeleted
        """
        delBills = iqe.getDeletedBills()
        for bill in delBills:
            derashBill = self.getBillDerash(bill)
            if len(derashBill) != 0:
                updateBill = {
                    "bill_id": derashBill["bill_id"],
                    "bill_desc": "Bill no longer payable",
                    "reason": "Paid or deleted",
                    "amount_due": derashBill["amount_due"],
                    "already_paid": True,
                    "due_date": datetime.today().strftime("%Y-%m-%d")
                }
                self.conn.request('PUT', '/biller/customer-bill-data', headers=self.headers, body=json.dumps(updateBill))



    def downloadPayment(self, iqe):
        """
        Download's all payments since the last unpaid bill from INSA Derash

        :param iqe: object of db access
        """
        fromDate = iqe.getMinUnpaidDate()
        toDate = datetime.today().strftime("%Y-%m-%d")

        self.conn.request('GET', f"/biller/customers-paid-bill?fromDate={fromDate}&toDate={toDate}", headers=self.headers)
        res = self.conn.getresponse()
        result = res.read().decode('utf-8')

        if res.status == 200:
            return result # this is csv format
        else:
            print(result)
            return {}