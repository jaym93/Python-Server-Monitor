Python-Server-Monitor
=====================

Background
----------

I write this Python script to monitor our synchronization servers to ensure they are always available, if not, it would send our team an email.
It uses Win32 libraries to run a command in the Windows CMD and scan the resulting output for the attributes you specify.

I have also added a Python dictionary for each check and parameter in case you want to further extend the script functionality.

