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

class RunCommand(cmd.Cmd):
 """ Simple shell to run a command on the host """
 prompt = 'Steelhead PowerCLI > '
 
 #override default cmd behaviour of running the last command when entering nothing
 def emptyline(self):
  pass
 
 def __init__(self):
  cmd.Cmd.__init__(self)
  self.hosts = []
  self.connections = []
  self.hostnames = []
  self.debug = False
  self.resolvedns = False
  self.pwd = ''
  self.user = ''

 def do_add_host(self, args):
  """add_host : Add a host to the host list."""
  if len(args.split(','))==3:
   self.hosts.append(args.split(','))
  elif (len(args.split(','))==1 and self.pwd != '' and self.user != ''):
   self.hosts.append([args,self.user,self.pwd])
  else:
   print "usage: add_host <ip>,<username>,<pwd> "
   print "usage: add host <ip> + make sure pwd and user settings are defined using set command"
   
 def do_set(self, args):
  """set debug on|off        : Set debug output on|off
set resolvedns on|off   : Resolve each IP address in output to DNS name
set user <user>         : Default username
set pwd <pwd>           : Default password"""
  l = args.split()
  if len(l) < 1:
   print "Set needs an argument. Do 'help set'"
   return
  if l[0] == 'debug' and l[1] == 'on': self.debug = True
  if l[0] == 'debug' and l[1] == 'off': self.debug = False
  if l[0] == 'resolvedns' and l[1] == 'on': self.resolvedns = True
  if l[0] == 'resolvedns' and l[1] == 'off': self.resolvedns = False
  if l[0] == 'user':
   if len(l) == 2: self.user = l[1]
   else: print ('Please provide username. set user <username>')
  if l[0] == 'pwd':
   if len(l) == 2: self.pwd = l[1]
   else: print ('Please provide password. set pwd <password>')
 

 def do_remove_host(self, args):
  """remove_host : Remove a host from the host list."""
  if args:
   log.info( "to be implemented")
  else:
   print "Usage: remove_host <ip> "
  
 def do_show(self, args):
  """show hosts     : View configured hosts
show opt       : Show optimized connections
show opt_ssl   : Show optimized SSL connections, aggregated per destination host
show pass      : Show passthrough connections
show preex     : Show preexisting sessions
show set       : Show settings"""
  l = args.split()
  if len(l) < 1:
   print "Show needs an argument. Do 'help show'"
   return
  if l[0] == 'set':
   log.info("debug = %s" % self.debug)
   log.info("resolvedns = %s" % self.resolvedns)
   log.info("user = %s" % self.user)
   log.info("pwd = %s" % self.pwd)
  
  
  if l[0] == 'hosts':
   log.info("Configured hosts")
   for lijn in self.hosts:
    log.info(lijn)
  elif (l[0] == 'opt') or (l[0] == 'pass') or (l[0] == 'preex'):
    #some preprocessing because argparser needs --
    cmdline = args
    cmdline = cmdline.replace('top', '--top')
    cmdline = cmdline.replace('tcp', '--tcp')
    cmdline = cmdline.replace('clients', '--clients')
    
    parser = argparse.ArgumentParser(prog='show')
    subparsers = parser.add_subparsers(help='commands')
    
    opt_parser = subparsers.add_parser('opt', help='Show optimized connections')
    opt_parser.add_argument('--top', nargs='?', help='top help')
    opt_parser.add_argument('--tcp', nargs='?', help='tcp help')
    opt_parser.add_argument('--clients', dest='clients', action='store_true')
    opt_parser.set_defaults(func='opt')
    opt_parser.set_defaults(clients=False)
    
    pass_parser = subparsers.add_parser('pass', help='Show passthrough connections')
    pass_parser.add_argument('--top', nargs='?', help='top help')
    pass_parser.add_argument('--tcp', nargs='?', help='tcp help')
    pass_parser.add_argument('--clients', dest='clients', action='store_true')
    pass_parser.set_defaults(func='pass')
    pass_parser.set_defaults(clients=False)
    
    preex_parser = subparsers.add_parser('preex', help='Show preexisting connections')
    preex_parser.add_argument('--top', nargs='?', help='top help')
    preex_parser.add_argument('--tcp', nargs='?', help='tcp help')
    preex_parser.add_argument('--clients', dest='clients', action='store_true')
    preex_parser.set_defaults(func='preex')
    preex_parser.set_defaults(clients=False)
      
    #parser.print_help()
    try:
     parsed_arg = parser.parse_args(cmdline.split())
    except SystemExit:
     #print ('do something else and continue')
     pass

    if (self.debug): print parsed_arg
    
    #set maximum if top is specified
    maximum = 0
    if (parsed_arg.top): maximum = parsed_arg.top
    if (self.debug): print maximum
    
    #default command assumed = opt
    cli_command = []
    cli_command.append('show connections optimized full\n')
    cli_command.append(' : Optimized Connections Overview')
    cli_command.append('O')
    
    if (parsed_arg.func == 'pass'):
     cli_command[0] = 'show connections passthrough\n'
     cli_command[1] = ' : Passthrough Connections Overview'
     cli_command[2] = 'PI'
     
    if (parsed_arg.func == 'preex'):
     cli_command[0] = 'show connections passthrough filter pre_existing\n'
     cli_command[1] = ' : Pre-existing Connections Overview'
     cli_command[2] = 'PI'
	
    for host, conn, naam in zip(self.hosts, self.connections, self.hostnames):
     log.info( naam + cli_command[1])
     log.info('------------------------------------------------')
     channel = conn.invoke_shell()
     channel.settimeout(10800)
     channel.send('term length 0\n')
     channel.send(cli_command[0])
     buff = ''
     while not buff.endswith('> '):
      resp = channel.recv(9999)
      buff += resp
      if (self.debug): log.debug("Buffer")
      if (self.debug): log.debug(buff)
     opt_conn = buff

     count = 0
     rij = []
     for line in StringIO.StringIO(opt_conn):
      line = line.replace("\n","")
      if line.startswith(cli_command[2]):
       parts = line.split()
       if (self.debug): log.debug("Parts")
       if (self.debug): log.debug(parts)
       source = parts[1]
       (sourceip,sourceport) = source.split(':')
       destination = parts[2]
       (destip,destport) = destination.split(':')
       protocol = parts[3]
	   #to be fixed: don't store time, datum, rate, is sometimes nonexisting with passthrough, when datum == pre_existing
       #rate = parts[4]
       #datum = parts[5]
       #tijd = parts[6]
       #print sourceip+" "+sourceport+" "+destip+" "+destport+" "+protocol
       rij.append(sourceip)
       rij.append(sourceport)
       rij.append(destip)
       rij.append(destport)
       rij.append(protocol)
       count = count + 1

      #only collect LAN/WAN statistics for optimized sessions
      if (parsed_arg.func == 'opt'):
       lan = []
       wan = []
       wan = re.findall(r'WAN: (\d*)KB', line)
       lan = re.findall(r'LAN: (\d*)KB', line)
      
       if (wan != []): 
        #print wan[0]
        rij.append(wan[0])
       if (lan != []):
        #print lan[0]
        rij.append(lan[0])
       
     if (parsed_arg.func == 'opt'): 
      # 7 parameters per row     
      multi = zip(rij[0::7],rij[1::7],rij[2::7],rij[3::7],rij[4::7],rij[5::7],rij[6::7])
     else:
      # 5 parameters per row
      multi = zip(rij[0::5],rij[1::5],rij[2::5],rij[3::5],rij[4::5])
     if (self.debug): log.debug(multi)
     #print multi[100]
     
     
     filtered = []
     #Execute additional filtering on TCP if tcp parameter is given
     if (parsed_arg.tcp):
      count = 0
      for line in multi:
       if (line[3] == parsed_arg.tcp):
        #print line
        filtered.append(line)
        count = count + 1
      multi = filtered  
    
     
     

     #AGGREGATE PER TCP
     #extract TCP ports out of array (TCP = index 3)
     aggregate = [x[3] for x in multi]
     
     #if tcp is specified, aggregate on destination IP address (index = 2) by default
     #if client option is specified, aggregate by client ip address instead
     #else nothing specified, TCP default
     if (parsed_arg.tcp) and not(parsed_arg.clients):
      aggregate = [x[2] for x in multi]
      log.info('Destination IP  : #')
     elif (parsed_arg.tcp) and (parsed_arg.clients):
      aggregate = [x[0] for x in multi]
      log.info('Client IP       : #')
     else: log.info('TCP             : #')
     
     
     
     log.info('--------------------------------------')
	
     #aggregate by nth element
     if (maximum == 0): 
      sumprot = Counter(aggregate)
      if (self.debug): print sumprot
      #print counter var (set to only take unique values)
      for element in set(sumprot.elements()):
       log.info('{0: <16}: {1: <16}'.format(element,sumprot[element]))
	 	 
     else:
      sumprot = Counter(aggregate).most_common(int(maximum))
      if (self.debug): print sumprot
	  #sumprot is now not a counterobject anymore, but notmal list
      for a,b in sumprot:
       log.info('{0: <16}: {1: <16}'.format(a,b))
    
     
     log.info('Total Sessions: ' + str(count))
     log.info("========== end of data ========= ")
	 
  elif l[0] == 'opt_ssl':
    for host, conn, naam in zip(self.hosts, self.connections, self.hostnames):
     log.info(naam + ' : Optimized SSL (TCP443) Connections Overview')
     log.info('------------------------------------------------------------')
     channel = conn.invoke_shell()
     channel.settimeout(10800)
     channel.send('term length 0\n')
     channel.send('show connections optimized\n')
     buff = ''
     while not buff.endswith('> '):
      resp = channel.recv(9999)
      buff += resp
      if (self.debug): log.debug(buff)
     opt_conn = buff

     count = 0
     rij = []
     for line in StringIO.StringIO(opt_conn):
      line = line.replace("\n","")
      if line.startswith('O'):
       parts = line.split()
       source = parts[1]
       (sourceip,sourceport) = source.split(':')
       destination = parts[2]
       (destip,destport) = destination.split(':')
       protocol = parts[3]
       rate = parts[4]
       datum = parts[5]
       tijd = parts[6]
       #print sourceip+" "+sourceport+" "+destip+" "+destport+" "+protocol
       if (destport == '443'):
        rij.append(sourceip)
        rij.append(sourceport)
        rij.append(destip)
        rij.append(destport)
        rij.append(protocol)
        count = count + 1

     multi = zip(rij[0::5],rij[1::5],rij[2::5],rij[3::5],rij[4::5])
     #print multi
     #print multi[100]

     #extract nth element in array
     protocols = [x[2] for x in multi]
	
     log.info('HOST           : #')
     log.info('---------------------------')
	
     #aggregate by nth element
     sumprot = Counter(protocols)
     #sumprot = counter object
     #print counter var (set to only take unique values)
     for element in set(sumprot.elements()):
      log.info('{0: <15}: {1: <6}'.format(element,sumprot[element]))
	 	 
     log.info('Total SSL Optimized Sessions: ' + str(count))
     log.info("========== end of data ========= ")





	 


 def do_connect(self, args):
  """Connect to all hosts in the hosts list"""
  for host in self.hosts:
   log.info("Trying to connect to "+host[0])
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   ssh.connect(host[0], username=host[1], password=host[2])
   self.connections.append(ssh)
   #Try to detect hostname
   channel = ssh.invoke_shell()
   channel.settimeout(10800)
   channel.send('term length 0\n')
   channel.send('show host\n')
   
   buff = ''
   while not buff.endswith('> '):
    resp = channel.recv(1000)
    buff += resp
   
   for line in StringIO.StringIO(buff):
     line = line.replace("\n","")
     if (self.debug): log.debug("L: "+line)
     if line.startswith('Hostname'):
      parts = line.split()
      if (self.debug): log.debug(parts)
      hostnaam = parts[1]
      log.info("Connection Successfull. Detected hostname "+hostnaam)
      self.hostnames.append(hostnaam)
   #print self.hostnames

 def do_run(self, command):
  """Execute normal CLI command on all hosts in the list"""
  if command:
   for host, conn, naam in zip(self.hosts, self.connections, self.hostnames):
    log.info(naam)
    log.info('---------------------------------')
    log.info('Running: ' + command)
    channel = conn.invoke_shell()
    channel.settimeout(10800)
    channel.send(command +'\n')
    buff = ''
    while not buff.endswith('> '):
     resp = channel.recv(9999)
     buff += resp

    log.info(buff)
    
	#stdin, stdout, stderr = conn.exec_command(command)
    #stdin.close()
    #for line in stdout.read().splitlines():
    # print 'host: %s: %s' % (host[0], line)
  else:
   print "Usage: run <command> "

 def do_close(self, args):
  """Close connections to all hosts in the hosts list"""
  for conn in self.connections:
   conn.close()

   

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fileformat = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
terminalformat = logging.Formatter("%(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(terminalformat)
log.addHandler(ch)

fh = logging.FileHandler("./rvbd.log")
fh.setFormatter(fileformat)
log.addHandler(fh)   

# Main Loop   
if __name__ == '__main__':
    RunCommand().cmdloop()

