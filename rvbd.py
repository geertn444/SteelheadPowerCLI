import paramiko
import time
import StringIO
import string
#from collections import Counter
import cmd
import logging
import logging.handlers
import sys
import argparse
import re
import json
import pandas as pd
import numpy as np

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

 def do_add(self, args):
  """add host : Add a host to the host list."""
  l = args.split()
  if len(l) < 1:
   print "Add needs an argument. Do 'help add'"
   return
  if l[0] <> 'host':
   print "Unknown argument. Do 'help add'"
   return
  tekst = l[1]
  if len(tekst.split(','))==3:
   self.hosts.append(tekst.split(','))
  elif (len(tekst.split(','))==1 and self.pwd != '' and self.user != ''):
   self.hosts.append([tekst,self.user,self.pwd])
  else:
   print "usage: add host <ip>,<username>,<pwd> "
   print "usage: add host <ip> + make sure pwd and user settings are defined using set command"
   
 def do_save(self, args):
  """save hosts     : Save hosts to default file hosts.txt"""
  l = args.split()
  if len(l) < 1:
   print "Save needs an argument. Do 'help save'"
   return
  if l[0] <> 'hosts':
   print "Unknown argument. Do 'help save'"
   return
  if self.hosts == []:
   print "Nothing to save. Add hosts with add_host or load hosts with load_hosts."
   return
  try:
   f = open('./hosts.txt', 'w')
   json.dump(self.hosts,f)
   f.close()
  except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
    return
  except:
    print "Unexpected error:", sys.exc_info()[0]
    return
  print json.dumps(self.hosts)  
  print "Hosts successfully written to file."
  
 def do_load(self,args):
  """load hosts      : Load hosts from default file hosts.txt"""
  l = args.split()
  if len(l) < 1:
   print "Load needs an argument. Do 'help load'"
   return
  if l[0] <> 'hosts':
   print "Unknown argument. Do 'help load'"
   return
  try:
   f = open('./hosts.txt', 'r')
   self.hosts = json.load(f)
   f.close()
  except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
    return
  except:
    print "Unexpected error:", sys.exc_info()[0]
    return
  print self.hosts
  print "Successfully loaded hosts."

  
 def do_exit(self,args):
  """exit : Exit PowerCLI"""
  return True
   
 def do_set(self, args):
  """set debug on|off        : Set debug output on|off
set resolvedns on|off   : Resolve each IP address in output to DNS name (not implemented yet)
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
 

 #def do_remove_host(self, args):
 # """remove_host : Remove a host from the host list [NOT IMPLEMENTED YET]."""
 # if args:
 #  log.info( "to be implemented")
 # else:
 #  print "Usage: remove_host <ip> "
  
 def do_show(self, args):
  """show hosts     : View configured hosts
show opt       : Show summary of optimized connections
show pass      : Show summary of passthrough connections
show preex     : Show summary of preexisting sessions
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
   return  
  
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
     log.info('---------------------------------------------------------')
     channel = conn.invoke_shell()
     channel.settimeout(10800)
     channel.send('term length 0\n')
     channel.send(cli_command[0])
     buff = ''
     while not buff.endswith('> '):
      resp = channel.recv(9999)
      buff += resp
      #if (self.debug): log.debug("Buffer")
      #if (self.debug): log.debug(buff)
     opt_conn = buff

     count = 0
     rij = []
     pandas_rij = []
     rijdict = {}
     
     for line in StringIO.StringIO(opt_conn):
      line = line.replace("\n","")
      if line.startswith(cli_command[2]):
       parts = line.split()
       rijdict = {}
       #if (self.debug): log.debug("Parts")
       #if (self.debug): log.debug(parts)
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
       rijdict.update({'sourceip': sourceip})
       #rij.append(sourceip)
       
       rijdict.update({'sourceport': sourceport})
       #rij.append(sourceport)
       
       rijdict.update({'destip': destip})
       #rij.append(destip)
       
       rijdict.update({'destport': destport})
       #rij.append(destport)
       
       rijdict.update({'protocol': protocol})
       #rij.append(protocol)
       count = count + 1

      #only collect LAN/WAN statistics for optimized sessions
      #note: these lan/wan statistics are on another line as the previous statistics (wan is first)
      #lan line concludes all data -> save
      #NOTE2: maybe it is better to make lan/wan columns always and fill them with 0 for passtrue sessions
      
      if (parsed_arg.func == 'opt'):
       lan = []
       wan = []
       wan = re.findall(r'WAN: (\d*)KB', line)
       lan = re.findall(r'LAN: (\d*)KB', line)
      
       
       if (wan != []): 
        #print wan[0]
        #rij.append(wan[0])
        #must change to integer in order to be able to aggregate later with pandas !
        rijdict.update({'wan': int(wan[0])})
       
       if (lan != []):
        #print lan[0]
        #rij.append(lan[0])
        #must change to integer in order to be able to aggregate later with pandas !
        rijdict.update({'lan': int(lan[0])})
        #conclude collection (if opt)
        pandas_rij.append(rijdict)
      
      else:      
       #not opt command, no need to collect lan/wan statistics
       #just conclude
       #copy row to array
       pandas_rij.append(rijdict)
      
     
     #convert to pandas dataframe
     df = pd.DataFrame(pandas_rij)
     
     
     
     
      
     
     
     
     #save df to disk (so i can analyse it easily further in ipython notebook :-)
     df.to_csv('./last.csv')
     
     #from now on, work only with pandas, comment out older (non-pandas) code
     
     #filtered = []
     #Execute additional filtering on TCP if tcp parameter is given
     if (parsed_arg.tcp):
      #count = 0
      df = df.convert_objects(convert_numeric=True)
      #just one simple line with pandas, destport must be int here, therefore above line
      df = df[df.destport == int(parsed_arg.tcp)]
     
     if (self.debug): log.debug(df.dtypes)
     if (self.debug): log.debug(df)
     

     #AGGREGATE PER TCP
     #extract TCP ports out of array (TCP = index 3)
     #aggregate = [x[3] for x in multi]
     
     #and sorted immediatly in pandas
     #pandas_a = df.groupby('destport').count().sort('destip',ascending=False)
     
     
     #get counts table
     count = df.groupby('destport')['destport'].count()
     #aggregate by destport (sum bytes in lan/wan) and drop sourceport column
     
     #result = df.groupby('destport').sum().drop('sourceport',1)
     #BUG NOTE: if sourceport is not converted to integer, it will be removed by the .sum and the .drop will give an error.....
     #code below is better
     
     result = df.groupby('destport').sum()
     if 'sourceport' in result.columns:
      #drop 'sourceport' but first check for existance
      result=result.drop('sourceport',1)
     
     #BUG NOTE: the index (destports) is again a string, and therefore prints ok during output
     #joint count table, column name will be destport, rename to count
     result = result.join(count).rename(columns = {'destport':'count'})
     #sort descending on count
     pandas_a = result.sort('count',ascending=False)
     
     
     #NOTE: LAN & WAN numbers are in KB , which is quiet large for some sessions
     #NOTE: some sessions have 0 KB WAN and 0 KB LAN -> should see if i can find a command that shows B instead of KB maybe
     #NOTE: some sessions have > LAN bytes then WAN bytes, in riverbed these are counted as 0% optimisation (which is actually false and will increase
     #optimisation rate of the protocol false positive)
     #NOTE: if we add them up to valid sessions, they will bring down the optimisation rate (which resembles more reality)
    
     
          
     
     #if tcp is specified, aggregate on destination IP address (index = 2) by default
     #if client option is specified, aggregate by client ip address instead
     #else nothing specified, TCP default (keep the above)
     if (parsed_arg.tcp) and not(parsed_arg.clients):
      #aggregate = [x[2] for x in multi]
      #pandas_a = df.groupby('destip').count().sort('destport',ascending=False)
      
      count = df.groupby('destip')['destip'].count()
      #aggregate by destip (sum bytes in lan/wan) and drop sourceport+destport column
      result = df.groupby('destip').sum().drop('sourceport',1)
      result = result.drop('destport',1)
      #joint count table, column name will be destport, rename to count
      result = result.join(count).rename(columns = {'destip':'count'})
      #sort descending on count
      pandas_a = result.sort('count',ascending=False)
     
      
      
      log.info('Destination IP  : #           : LAN KB      : WAN KB      : KB Saved    : Opt Rate')
     elif (parsed_arg.tcp) and (parsed_arg.clients):
      #aggregate = [x[0] for x in multi]
      #pandas_a = df.groupby('sourceip').count().sort('sourceport',ascending=False)
      
      count = df.groupby('sourceip')['sourceip'].count()
      #aggregate by sourceip (sum bytes in lan/wan) and drop sourceport+destport column
      result = df.groupby('sourceip').sum().drop('sourceport',1)
      result = result.drop('destport',1)
      #joint count table, column name will be destport, rename to count
      result = result.join(count).rename(columns = {'sourceip':'count'})
      #sort descending on count
      pandas_a = result.sort('count',ascending=False)
      
      log.info('Client IP       : #           : LAN KB      : WAN KB      : KB Saved    : Opt Rate')
     else: log.info('TCP             : #           : LAN KB      : WAN KB      : KB Saved    : Opt Rate')
     
     
     #calculate optimisation rates -only- when viewing optimized sessions
     if (parsed_arg.func == 'opt'):
      #make sure lan/wan are integer
      pandas_a = pandas_a.convert_objects(convert_numeric=True)
      pandas_a['kbsaved']=pandas_a['lan']-pandas_a['wan']
      pandas_a['rate']=100*pandas_a['kbsaved']/pandas_a['lan']
     
     
     if (self.debug): log.debug(pandas_a)
     if (self.debug): log.debug(pandas_a.dtypes)
     
     log.info('---------------------------------------------------------------------------------------------')
	
     
     #maximum = top parameter; 0 = print all, <> 0 = print only top x records
     if (maximum <> 0): 
      #truncate to top <maximum> records
      pandas_a = pandas_a.head(int(maximum))
     
     
     if (self.debug): log.debug(pandas_a)     
      
     #note: instead of iterating row by row, we can also just print the darn thing with only one column and the column name changed
     #formatting is done by pandas by default  (maybe for future versions)
     for index, row in pandas_a.iterrows():
      if (parsed_arg.func == 'opt'):
       log.info('{0:<16}: {1:<12.0f}: {2:<12.0f}: {3:<12.0f}: {4:<12.0f}: {5:<12.2f}'.format(index,row['count'],row['lan'],row['wan'],row['kbsaved'],row['rate']))
      else:
       log.info('{0:<16}: {1:<12.0f}'.format(index,row['count']))
     
     som = pandas_a.sum()
     log.info('---------------------------------------------------------------------------------------------')
     if (parsed_arg.func == 'opt'):
      log.info('Totals          : {0:<12.0f}: {1:<12.0f}: {2:<12.0f}: {3:<12.0f}: {4:<12.2f}'.format(som['count'],som['lan'],som['wan'],som['kbsaved'],100*(som['lan']-som['wan'])/som['lan']))
     else:
      log.info('Totals          : {0:<12.0f}'.format(som['count']))
     log.info("========== end of data ========= ")

  # --
  # -- removed "show opt_ssl" command, use "show opt tcp 443" instead which is just the same	 
  # --
  
  else: log.info('Unknown argument. Use help show to see syntax.')




	 


 def do_connect(self, args):
  """connect       : Connect to all hosts in the hosts list"""
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
  """run <command>     : Execute normal CLI command on all hosts in the list"""
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
  """close           : Close connections to all hosts in the hosts list"""
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

