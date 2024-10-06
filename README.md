# Bronze
An HTTP client that syncs data with an external RESTful API which is INSA's Derash.


## Dependencies
Requires `pyodbc` library for database access.
`pip install pyodbc`
should globally install the library

## Configuration
`appsettings.json` is used to configure the program startup parameters. 
`Derash` key object consists of the parameters that is required to connect with INSA Derash services. 
It consists of `domain` which is url address for INSA Derash usually has an address `https://api.derash.gov`
`apiSecret` and `apiKey` are values provided from INSA Derash per every integration.
`Database` is a connection string for the database.
`Town` this is the utility town name and used to generate unique bill_id's for Derash upload.
`WSIS` this is a WSIS parameter description such as it's address, port, username and password for
payment center access.

## Misc
`scripts.json` is a key value pair file that store's SQL statments mapped to a name for later access.
This should keep scripts out of the program's way.

## Run
Type the following on command prompt or linux shell. Built using Python 3.xx.
`python INTAPSBronze\main.py`

## Internals
### iQE
This is a database interface using `pyodbc` library. It's used to access the database using ODBC
calls, this would imply that any database can be used besides SQL Server which provides an ODBC library.
To interface with database it uses precooked queries from file `scripts.json`. This allows the object
to stay clear of any SQL syntax and makes it easy to modifiy the quries to the needs at hand without 
changing the code much.
#### attributes
`connStr - the connection string (see pyodbc connection string stuff)`
`conn - abstracts the connection object`
`qweries - holds a list of cooked queries from file 'scripts.json'`
`connected - boolean state of the database, True for connected`
#### iQE.connect
Start's connection with Database server given it's connection string, which is initalized when object
is instanstiated
#### iQE.disconnect
Tear's down the active DB connection using it's `conn` object
#### iQE.loadScripts
Load's cooked SQL queries from file `scripts.json` which stores SQL Statments as key-value pairs. The values
are stored as array of strings so as to make it human-readable. Key's are immutable and cannot be changed
as the program depends on those, however values can be updated as desired.
#### iQE.getUnpaidBills
Returns a list of unpaid bills that exist in the town (utlity) since the begining of time; i.e. it looks into
`customerBill` table and collects all those who's bills are not paid yet.
#### iQE.getCurrentPeriod
Return's the current bill period. This period is the period for the next bill sales.
#### iQE.getDeletedBills
Return's a list of deleted bills in the system. WSIS store's all deleted bills in *_deleted tables. Thus such
bills can be used to invalidate existing uploaded bills if not already paid from INSA Derash.
#### iQE.getMinUnpaidDate
Return's the minimum date for unpaid bill. This is used to query for paid bills in INSA Derash, since the
minimum unpaid bill date is the minimum bill date required to get bills, we are guranteed that all bills since
that period would be included. However, the process may be redundunt as Derash simply returns all bills since
that date paid or not.
#### iQE.getSettledBills
Given a billID this function returns all unsettled bills for a customer, thus payment could be made on all during
posting bills to WSIS.
#### iQE.getDueDate
Return's the last date for a bill payment allowed by INSA Derash, this date is normally the last date before
the toDate of the current period or the last date before the start of the next period.


### DerashClient
The object contains in it every functionality required to interface with INSA Derash and begin
downloading and uploading water services payment bills. 
#### attributes
`domain - domain name for the API provider (i.e. api.derash.gov.et without the https://)`
`port - the port number for API provider, defaults to 443 SSL port`
`conn - the connection object`
`town - utiltiy name or town name, used in unique id generation from tabluar id's`
`state - boolean value to track connected state of object`
Attributes are initalized to a default value during object instantiation.
#### DerashClient.Connect
This method starts an HTTPS connection with INSA Derash RESTful services and set's its internal
status to connected. It maintains the `conn` connection object for later access.
It uses `http.client.HTTPSConnection(address, port)`.
#### DerashClient.Disconnect
It tears down the client connection using it's `conn` object. It also set's its internal state
to disconnected or False.
#### DerashClient.uploadDerash
This function makes use of `iQE` object to access the database. The aim of this function is double
fold, it acquires a list of all the unpaid bills along with the current period and dueDate, it then
check's to see if any of these bills have already been uploaded to Derash using `DerashClient.getBillDerash`
if bill is found it updates the bill info using `DerashClient.updateDerash`, if not it uploads it
as a new bill using `DerashClient.uploadNewDerash`.
#### DerashClient.updateDerash
Update's existing bills on Derash. It checks if the new bill amount and Derash bill amount is same
if not it upload's the update using Derash `PUT` request. The concept here is, Derash aggregates bills
thus if a new bill has been added in WSIS or removed from WSIS or amount changed due to reading correction
and stuff, this aggregate bill in Derash can be identifed using one of the ID's of the indiviual bills for
WSIS - since whatever exists in Derash has to be subset of all the unpaid bill IDs for an indvidual. However,
the query does help here as it orders bills based on their post date, thus Bronze would naturally send and reterive
the first list of ID's returned from WSIS Database as an id for Derash. Combining the id with the Town name
gurantees uniqueness on Derash since no bill Id can be repeated.
#### DerashClient.getBillDerash
Checks to see if a bill sent as it's parameter exists in INSA Derash databases by using it's bill ID. It scans
for all unpaid bill id list to check if each of the bills has not been uploaded to Derash before. Normally, however
the query gurantees that it would be the first element in the aggregated id's returned from WSIS database. If the
bill does not exist in Derash it return's an empty object signalling the caller that it can uploadBill as new,
alas the bill info would be returned to signal the caller to update bill info instead.
#### DerashClient.uploadNewDerash
This function upload's the bill sent as a parameter along side dueDate and period as JSON formatted info for
Derash. It uses the first id among the aggregated id's (comma separted list of id see `qryUnpaidBills` in `scripts.json`)
combined with the town name to gurantee uniquness and avoid uploads & confilcts with/of older system DerashRouter.
#### DerashClient.invalidateBill
Removes/deactivates bills in Derash that have been removed from WSIS. This function only works if the bill deleted
in WSIS is the first bill for unpaid bills of a customer, if not the more suitable method of `DerashClient.updateDerash`
can be used for such instances, which includes all unpaid bills for a customer as aggregate.
#### DerashClient.downloadPayments
Download's all payments made in Derash since the minimum upaid bill date for a utility, that way we are sure to
include all bills that have been paid since then even if time has lapased without sync due to someother problem.
This seeks to avoid the problem of INTAPS DerashRouter v1.0 which checks bills from the date of the last sync. This
can sometimes lead to problems of unsynced bills becuase time has lapsed without updating certain bills due to network
failure or bug in the system and brings the overhead of manually tracking dates for download.

### WSISClient
Used to interface with good ol' WSIS Server.
#### attributes
`sessionID - WSIS sessionID, acquired as a result of successful connection`
`conn - abstract's the connection object using http.client.HTTPConnection`
`state - a boolen value indicating the state of WSIS server connection`
`paymentcenter - holds WSIS payment centers`
`username - WSIS system username for later access`
#### WSISClient.connect
Start's connection with WSIS Server at TCP/IP level. Set's the internal state to connected. It initailzes it's
`conn` attribute using `http.client.HTTPConnection` object.
#### WSISClient.disconnect
Tear's the active connection down using it's `conn` member.
#### WSISClient.startSession
Authenticates with WSIS Server and acquire's it's session id for later use.
#### WSISClient.getPaymentCenter
Reterive's a list of all the payment center's for a town from WSIS databases. This function is Obselete and its 
no longer useful.
#### WSISClient.postBillPayment
Post's a bill payment to WSIS using it's PostBill API and session id. When it comes to saving payment records
Bronze has elected already use the existing WSIS infrastructure no matter how slow it may be for maximum safety.
#### WSISClient.dateToTicks
This a utlity function used to roughly convert Python datetime format into C# datetime.Ticks format using a pre-defined
formula obtained from stackoverflow.com