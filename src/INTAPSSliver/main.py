# File Desc: The driver module for Adulis app
#
# Program Author: Rediet Worku aka Aethiops II ben Zahab
#
# Date Created: 21st of Septemeber 2024, Saturday
import http.client
import json

from derash_client import DerashClient
from iqe import iQE



def Main():
    """
    The arena
    """
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

        print('Bronze: Uploading bills to INSA Derash API.')
        #derash_client.uploadDerash(iqe)
        derash_client.downloadPayment(iqe)
        
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