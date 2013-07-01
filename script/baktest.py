'''
Created on 2013-3-29

@author: Administrator
'''


import os, sys, time, signal
import gio, gobject, glib
from apscheduler.scheduler import Scheduler

from nsccdbbak.common.configFilePraser import ConfigFilePraser
from nsccdbbak.common.connDatabase import ConnDatabase

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

curdir = os.getcwd()
pardir = os.path.dirname(curdir)    
filepath = pardir + "\\conf\\Policy.conf"
    
sched = Scheduler()
sched.daemonic = False
sched.start()   

def glob_bak(self):
    timestr = time.strftime(r"%Y-%m-%d_%H-%M-%S", time.localtime())
    print timestr
    tmpFile = file("E:\\temp.txt", 'a+')
    tmpFile.write(timestr + '\n')
    tmpFile.close    
    
def incr_bak(self):
    pass


policyconfig = ConfigFilePraser(filepath)       
policys = policyconfig.load(12)
for dictTmp in policys:
    if dictTmp['flag'][0] == '1':
        for key in dictTmp.keys():
            if dictTmp[key][0] == '':
                dictTmp[key][0] = None
        glob_bak_name = 'glob_bak_' + dictTmp['server'][0]
        sched.add_cron_job(glob_bak, month=dictTmp['globmonth'][0], day=dictTmp['globday'][0], 
                                day_of_week=dictTmp['globweekday'][0], hour=dictTmp['globhour'][0], 
                                minute=dictTmp['globminute'][0], second='*/3', name=glob_bak_name)
        incr_bak_name = 'incr_bak_' + dictTmp['server'][0]
        sched.add_cron_job(incr_bak, month=dictTmp['incmonth'][0], day=dictTmp['incday'][0], 
                                day_of_week=dictTmp['incweekday'][0], hour=dictTmp['inchour'][0], 
                                minute=dictTmp['incminute'][0], name=incr_bak_name)
print sched.get_jobs()
print 'init_sched finished!'



    
#class fileModifiedHandler(FileSystemEventHandler):
#    def __init__(self, fileptah=None):
#        if filepath == None:
#            self.filepath = os.getcwd()
#        else:
#            self.filepath = filepath
#        pass
#        
#    def on_modified(self, event):
#        for job in sched.get_jobs():
#            if job.name != 'watchdog':
#                sched.unschedule_job(job)
#        
#        assign_jobs(self.filepath)
#    
#def assign_mointor():
#    sched.add_interval_job(init_watchdog, name = 'watchdog')
#    print sched.get_jobs()
#    
#def init_watchdog(filepath):
#    observer = Observer()
#    event_handler = fileModifiedHandler()
#    observer.scheduler(event_handler, filepath, recursive=True)
#    observer.start()
#    observer.join()    
                          
    

