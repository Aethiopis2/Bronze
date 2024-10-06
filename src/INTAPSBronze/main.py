# File Desc: The driver module for Adulis app
#
# Program Author: Rediet Worku aka Aethiops II ben Zahab
#
# Date Created: 21st of Septemeber 2024, Saturday
import http.client
import json
import time

from derash_client import DerashClient
from iqe import iQE
from wsis_client import WSISClient


SLEEP_TIME = 10

def Main():
    """
    The arena
    """
    running = True
    try:
        print("Bronze: Initializing.")
        with open('appsettings.json', 'r') as file:
            config = json.load(file)

        print("Bronze: Connecting to database.")
        iqe = iQE(config["Database"]["connectionString"])
        iqe.connect()
        iqe.loadScripts()
        
        print('Bronze: Connecting to INSA Derash API.')
        domain = config["Derash"]["domain"]
        apiKey = config["Derash"]["apiKey"]
        apiSecret = config["Derash"]["apiSecret"]
        utilityTown = str(config["Town"]).upper() + '-'
        derash_client = DerashClient(domain, apiKey, apiSecret, utilityTown)
        derash_client.connect()

        print("Bronze: Connecting to WSIS Server.")
        host = config["WSIS"]["server"]
        port = config["WSIS"]["port"]
        uname = config["WSIS"]["username"]
        pwd = config["WSIS"]["password"]
        wsis = WSISClient()
        wsis.connect(host, port)
        if wsis.startSession(uname, pwd) == False:
            print("Bronze: WSIS session failed, please check username and password.")
            running = False
        else:
            wsis.getPaymentCenter()
        
        while running:
            print('Bronze: Uploading bills to INSA Derash API.')
            #derash_client.uploadDerash(iqe)

            print("Bronze: Downloading payments from INSA Derash.")
            payments = derash_client.downloadPayment(iqe)
            print(f"Bronze: Found {len(payments)} payment bills from INSA Derash.")

            if len(payments) > 0:
                print("Bronze: Posting payment bills to WSIS.")
                wsis.postBillPayment(payments, iqe, config["CashAccount"], config["AssetID"], utilityTown)

            print('Bronze: Sleeping for', SLEEP_TIME, 'seconds.')
            time.sleep(SLEEP_TIME)

    except http.client.HTTPException as e:
        print('Bronze HTTP exception: ', e)
    except Exception as e:
        print("Bronze generic exception occured: ", e)
    finally:
        if 'iqe' in locals() or 'iqe' in globals():
            iqe.disconnect()

        if 'derash_client' in locals() or 'derash_client' in globals():
            derash_client.disconnect()


if __name__ == '__main__':
    Main()