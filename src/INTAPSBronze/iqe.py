# File Desc: definition for iQE class, that is a minimal database interface 
#   using pyodbc library to connect with SQL Server
#
# Program Author: Rediet Worku aka Aethiops II ben Zahab
#
# Date Created: 21st of Septemeber 2024, Saturday
import pyodbc
import json


class iQE:
    """
    iNTAPS Query Engine is a mimimal database accessor class using
    pyodbc library to communicate with the database server
    """
    def __init__(self, connectionString):
        """
        constructor
        """
        self.connStr = connectionString
        self.conn = None
        self.qweries = {}
        self.connected = False


    def connect(self):
        """
        Connects to a RDBMS using the initalized parameters 
        """
        self.conn = pyodbc.connect(self.connStr)
        self.connected = True


    def disconnect(self):
        """
        Exit's the connection
        """
        if self.connected == True:
            self.conn.close()
        self.connected = False


    def loadScripts(self):
        """
        Load's the external SQL scripts or T-SQL statments from file 
        """
        with open('scripts.json', 'r') as file:
            self.qweries = json.load(file)


    def getUnpaidBills(self):
        """
        Get's all unpaid bills that exist in WSIS database regardless of time

        :return bill: a list of all unpaid bills that are in WSIS Subscriber Database
        """
        if self.connected == False:
            return -1
        
        bills = []
        cur = self.conn.cursor()
        cur.execute(' '.join(self.qweries["qwery"]["qryUnpaidBills"]))
        columns = [column[0] for column in cur.description]

        rows = cur.fetchall()
        for row in rows:
            bills.append(dict(zip(columns,row)))
        
        cur.close()
        return bills
    

    def getCurrentPeriod(self):
        """
        The current bill period is stored in SysParameters of Subscriber's database, 
        the function read's and return's the current bill period as human readable string
        and not by its id, Bronze has no use of period IDs.

        :return: the current bill period as human readable string
        """
        if self.connected == False:
            return -1
        
        cur = self.conn.cursor()
        cur.execute(' '.join(self.qweries["qwery"]["qryCurrentPeriod"]))
        rows = cur.fetchall()

        cur.close()
        return rows[0][0]
    

    def getDeletedBills(self):
        """
        Return's all the deleted bills from WSIS database, this is used to invalidate
        existing bills

        :return deleted: bills list on success alas -1 on fail
        """
        if self.connected == False:
            return -1
        
        cur = self.conn.cursor()
        cur.execute(' '.join(self.qweries["qwery"]["qryCurrentPeriod"]))
        columns = [column[0] for column in cur.description]

        rows = cur.fetchall()
        deleted = []
        for row in rows:
            deleted.append(dict(zip(columns, row)))

        cur.close()
        return deleted
    

    def getMinUnpaidDate(self):
        """
        :return date: get's the minimum of date for the unpaid bills
        """
        if self.connected == False:
            return -1
        
        cur = self.conn.cursor()
        cur.execute(' '.join(self.qweries["qwery"]["qryMinUnpaidBillDate"]))

        rows = cur.fetchall()
        cur.close()
        return rows[0][0]
    

    def getSettledBills(self, billID):
        """
        Get's the number of unpaid bill ID's given an initial billID for a given
        customer payment data.
        
        :param billID: the bill id for a customer
        """
        ids = []
        if self.connected == False:
            return
        
        cur = self.conn.cursor()
        qwery = ' '.join(self.qweries["qwery"]["qrySettledBills"])
        cur.execute(qwery.replace("@bid", str(billID)))
        #print(qwery.replace("@bid", str(billID)))
        rows = cur.fetchall()
        for row in rows:
            ids.append(row[0])

        cur.close()
        return ids
    

    def getDueDate(self, pid):
        """ Given its period ID returns the last date for payment or due date from
        it's 'toDate' feild. The previous day from this feild is the due date or last
        payment date allowed before the next bill period opens and upload's it's bills
        
        :param pid: the period id for current period
        """
        if self.connected == False:
            return
        
        cursor = self.conn.cursor()

        qwery = ' '.join(self.qweries["qwery"]["qrySettledBills"])
        cursor.execute(qwery.replace("@pid", str(pid)))

        rows = cursor.fetchall()
        cursor.close()
        return rows[0][0]