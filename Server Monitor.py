__author__ = 'jaym93'
__version__ = '1.0'
__date__ = '18-07-2015'

import urllib.request
import subprocess
import pymssql      # change SQL server module here, use pymysql for mysql, change it in the database check section also
import re
from time import gmtime, strftime
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# log files location, change location if necessary, make sure files exist before deployment
logFile = open('C:\\sniff.log', 'a')        # remember to clean out log files once in a while, it may take up too much space
errFile = open('C:\\error.log', 'a')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# server URLs here
serverUrlFoo = 'https://server-one.example.com:port1/fooService'
serverUrlBar = 'https://server-two.example.com:port2/barService'
# add more servers here, if necessary

try:
    # get HTTP response, 200 is OK
    responseFoo = urllib.request.urlopen(serverUrlFoo, context=ctx).getcode()
    responseBar = urllib.request.urlopen(serverUrlBar, context=ctx).getcode()
    # record time to the log
    logFile.write(strftime("%d/%m/%Y %H:%M:%S", gmtime()) + " - Server One:" + str(responseFoo) + ", Server Two:" + str(responseBar))
    if responseFoo == 200 or responseBar == 200:
        logFile.write(" -success\n")
    else:
        raise Exception('Cannot connect')

except Exception:       # deliberate wide exception catching, you want to get notified if ANYTHING goes wrong

    logFile.write(" -failure\n")
    emailContent = ""       # initialize email content

    # the following dictionary contains booleans for success / failure for each test
    results = {'proc': True, 'svc': True, 'port': True, 'dbms': True}
    emailContent += "We have detected a problem with one of your servers server. Please check your processes processes."
    emailContent += ("\n\nServer Foo returned HTTP code " + str(responseFoo) + " and server Bar returned HTTP code " + str(responseBar))

    ##########################################################
    ############ Command run interface (win-cmd) #############
    ##########################################################

    # this function uses Win32 subprocess to execute a command on the command line and iteratively return the output of the command
    def run_command(command):
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return iter(p.stdout.readline, b'')

    ##########################################################
    ############ Check if services are running ##############
    ##########################################################

    emailContent += "\n\n# SERVICE CHECK #"
    svcList = ['ServiceOne', 'ServiceTwo']      # put service names you want to check here
    svcResult = {'svcOne': False, 'svcTwo': False}      # this dictionary contains booleans for each of the services specified in the list above
    res = run_command("sc query \"" + svcList[0] + "\"")        # query for each of the services in the list
    for line in res:
        if re.findall("        STATE              : 4  RUNNING", line.decode()):        # check for 'running' status on each service
            svcResult['svcOne'] = True
            emailContent += "\n - service one running"
    res = run_command("sc query \"" + svcList[1] + "\"")
    for line in res:
        if re.findall("        STATE              : 4  RUNNING", line.decode()):
            svcResult['svcTwo'] = True
            emailContent += "\n - service two running"
    if not (svcResult['svcOne'] and svcResult['svcTwo']):
        emailContent += "\n<< Service check failed! >>"
        results['svc'] = svcResult

    ##########################################################
    ########## Check if console ports are listening ##########
    ##########################################################

    emailContent += ("\n\n# PORT CHECK #")
    portCheck = 'netstat -na'.split()   # check the ports using netstat
    port = run_command(portCheck)
    portResult = {'portOne': False, 'portTwo': False}       # boolean dictionary to store results
    for line in port:
        if re.findall("TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING", line.decode()):     # replace 8000 with port number
            emailContent += "\n - port one listening"
            portResult['portOne'] = True
        if re.findall("TCP    0.0.0.0:8001           0.0.0.0:0              LISTENING", line.decode()):     # replace 8001 with port number
            emailContent += "\n - port two listening"
            portResult['portTwo'] = True
    if not (portResult['portOne'] and portResult['portTwo']):
        emailContent += "\n<< Port check failed! >>"
        results['port'] = portResult

    ##########################################################
    ############# Check if processes are running #############
    ##########################################################

    emailContent += "\n\n# PROCESS CHECK #"
    processCheck = 'tasklist /svc /fo csv'.split()      # export tasks list + services as a CSV
    process = run_command(processCheck)
    procList = ['serverProc1', 'serverProc2', 'dbProcess', 'sqlFrontendProcess', 'reportingServerProcess']      # specify process name as a substring
    procResult = {'serverProc1': False, 'serverProc2': False, 'mssql': False, 'sqlagent': False, 'reports': False}      # boolean dictionary to store results of each process
    for line in process:
        if re.findall(procList[0], line.decode()):
            emailContent += "\n - server process one up"
            procResult['serverProc1'] = True
        if re.findall(procList[1], line.decode()):
            emailContent += "\n - server process two up"
            procResult['serverProc2'] = True
        if re.findall(procList[2], line.decode()):
            emailContent += "\n - SQL server up"
            procResult['mssql'] = True
        if re.findall(procList[3], line.decode()):
            emailContent += "\n - SQL agent up"
            procResult['sqlagent'] = True
        if re.findall(procList[4], line.decode()):
            emailContent += "\n - Reporting services up"
            procResult['reports'] = True
    if not (procResult['serverProc1'] and procResult['serverProc2'] and procResult['mssql'] and procResult['sqlagent'] and procResult['reports']):
        emailContent += "\n<< Process check failed! >>"
        results['proc'] = procResult

    ##########################################################
    ########## Check database connectivity (MSSQL) ###########
    ##########################################################

    emailContent += "\n\n# DB CONNECTIVITY CHECK #"
    dbmsResult = {'dbInstance1': True, 'dbInstance2': True}
    conOne = pymssql.connect('dbServerUrl1', 'userName1', 'password1', 'databaseName1')
    curOne = conOne.cursor()
    conTwo = pymssql.connect('dbServerUrl1', 'userName2', 'password2', 'databaseName2')
    curTwo = conTwo.cursor()
    try:
        curOne.execute("SELECT TOP 1 * FROM some_table")
    except:
        dbmsResult['dbInstance1'] = False

    try:
        curTwo.execute("SELECT TOP 1 * FROM some_table")
    except:
        dbmsResult['dbInstance2'] = False
    if dbmsResult['dbInstance1']:
        emailContent += ("\n - database instance one connected")
    if dbmsResult['dbInstance2']:
        emailContent += ("\n - database instance two connected")
    if not (dbmsResult['dbInstance1'] and dbmsResult['dbInstance2']):
        emailContent += ("\n<< DB Connectivity check failed! >>")
        results['dbms'] = dbmsResult

    ##########################################################
    ############# Report errors if any by email ##############
    ##########################################################

    emailContent += "\n\n This mailbox is not monitored, please do not reply to this email"
    msg = MIMEMultipart()
    msg['Subject'] = 'Server monitoring: Sync failure on server name'
    msg['From'] = 'monitoring@email.com'
    msg['To'] = 'recipient@email.com'
    body = MIMEText(emailContent)
    msg.attach(body)
    print(body)
    server = smtplib.SMTP('smtp.email.com')
    server.sendmail('monitoring@email.com', ['recipient1@email.com', 'recipient2@email.com'], msg.as_string())
    server.quit()
logFile.close()
errFile.close()
