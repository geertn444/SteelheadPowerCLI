# SteelheadPowerCLI Python Script

- Form factor: standard cli like
- Run any standard command on multiple Steelheads at the same time.
- Also contains "custom" made commands which the standard CLI is lacking.
    Display sessions per HTTP destination server.
    Limit results to top x servers/clients.
    Aggregate results per port, per client or per server (number of sessions)

WARNING: This code is beta code. Use at your own risk.
WARNING: This code does not contain a lot of error checks, so can/will crash on wrong imput.

# OS

For Python 2.7.8

# Release history

v0.1 : First version
v0.2
 You can now save your host list and load it from file
 Added 'exit' command to exit shell
v0.3
 Reworked statistics analysis to Pandas module.
 The script now has an additional dependecy on pandas module
 Reworked the "add_hosts" command to "add hosts", removing "_" from commands for consistency
 Removed the "show opt_ssl" command, use "show opt tcp 443", which is just the same

 


# Dependencies
# Paramiko requires Visual C++ for Python, available here: http://www.microsoft.com/en-us/download/details.aspx?id=44266

import paramiko
import pandas
import numpy
import time
import StringIO
import string
from collections import Counter
import cmd
import logging
import logging.handlers
import sys
import argparse
import re

# Usage

help                              ! Display some help
add host <ip>,<username>,<pwd>    ! Add a host
add host <ip>,<username>,<pwd>    ! Add a host
show hosts                        ! Show configured hosts
connect                           ! Initialise SSH sessions to hosts
show opt                          ! Basic overview of optimized sessions agg per destination server (on all hosts)
show pass                         ! Basic overview of passthrough sessions agg per destination server (on all hosts)
show opt tcp 80 top 5             ! Show top 5 HTTP servers with most optimised connections (on all hosts)
show opt tcp 443                  ! Show overview of optimized HTTPS sessions (on all hosts)
show opt tcp 443 clients top 10   ! Show the top 10 clients that have the most tcp 443 optimized connections (on all hosts)
show preex                        ! Show overview (aggregate) of pre-existing sessions per destination server (on all hosts)

# Work to be done

- aggregate optimisation statistics (ie optimisation rate etc)
- mass reset pre-existing sessions
- MUCH more error checking on wrong inputs
- etc...
