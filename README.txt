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

# Dependencies

import paramiko
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
add_host <ip>,<username>,<pwd>    ! Add a host
add_host <ip>,<username>,<pwd>    ! Add a host
show hosts                        ! Show configured hosts
connect                           ! Initialise SSH sessions to hosts
show opt                          ! Basic overview of optimized sessions agg per destination server (on all hosts)
show pass                         ! Basic overview of passthrough sessions agg per destination server (on all hosts)
show opt tcp 80 top 5             ! Show top 5 HTTP servers with most optimised connections (on all hosts)
show opt tcp 443                  ! Show overview of optimized HTTPS sessions (on all hosts)
show opt tcp 443 clients top 10   ! Show the top 10 clients that have the most tcp 443 optimized connections (on all hosts)
show preex                        ! Show overview (aggregate) of pre-existing sessions per destination server (on all hosts)

# Work to be done

- save and load host list
- aggregate optimisation statistics (ie optimisation rate etc)
- mass reset pre-existing sessions
- MUCH more error checking on wrong inputs
- convert to pandas module for statistics/aggregation calculation
- etc...
