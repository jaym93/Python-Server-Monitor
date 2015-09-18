# Python-Server-Monitor

## Background

I wrote this Python script to monitor our synchronization servers to ensure they are always available, if not, send the production support team an email.
It uses Win32 libraries to run a command in the Windows CMD and scan the resulting output for the attributes you specify.

I have also added boolean dictionaries for each check and parameter in case you want to further extend the script functionality.

## Current checks
Currently, this script performs 4 types of checks:
* **Process check:** checks if the process(es) specified are in RUNNING state
* **Port check:** checks if the specified ports (specified *8000* and *8001* in the script)   are in LISTENING state
* **Service check:** checks if the specified substrings (for example, *JBoss-8000* and *Tomcat7-8001*) are started
* **Database connectivity check:** checks if the specified database (server, username, password and database name to be specified) are available by running a select query on some table.

## Email server
Obtain the address of your SMTP mail server from your IT admin, use any custom email address for the 'from' field.
Specify the recipients in the array in `server.sendmail` statement.

## Best practices
There are sometimes timeouts, it is best if you hit the panic button for two consecutive missed heartbeats.
Schedule the script to 5 minute intervals in Windows Task Scheduler and it will monitor your services as long as the script is running.

