'''
Created on 2013-3-29

@author: Administrator
'''
#import os,sys
#
#curdir = os.getcwd()
#print curdir
#scriptfile = curdir + '\\script\\mysqlCron.py'
#
#r = os.system('python ' + scriptfile + ' start')
#print r
#
#a=None
#b=a
#print a, b

import os, time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from nsccdbbak.common.configFilePraser import ConfigFilePraser



class fileModifiedHandler(FileSystemEventHandler):   
    def init_sched(self):
        curdir = os.getcwd()
        pardir = os.path.dirname(curdir)    
        filepath = pardir + "\\conf\\Policy.conf"
        self.policyconfig = ConfigFilePraser(self.filepath) 
        policy = self.policyconfig.load(12)
        for dictTmp in policy:
            if dictTmp['flag'][0] == '1':
                for key in dictTmp.keys():
                    if dictTmp[key][0] == '':
                        dictTmp[key][0] = None
                glob_bak_name = 'glob_bak_' + dictTmp['server'][0]
                sched.add_cron_job(self.glob_bak, month=dictTmp['globmonth'][0], day=dictTmp['globday'][0], 
                                         day_of_week=dictTmp['globweekday'][0], hour=dictTmp['globhour'][0], 
                                         minute=dictTmp['globminute'][0], second='*/3', name=glob_bak_name)
                incr_bak_name = 'incr_bak_' + dictTmp['server'][0]
                sched.add_cron_job(self.incr_bak, month=dictTmp['incmonth'][0], day=dictTmp['incday'][0], 
                                         day_of_week=dictTmp['incweekday'][0], hour=dictTmp['inchour'][0], 
                                         minute=dictTmp['incminute'][0], name=incr_bak_name)
        print sched.get_jobs()
        print 'init_sched finished!'
    
    def on_modified(self, event):
        for job in sched.get_jobs():
            sched.unschedule(job)
        self.init_sched()
        pass

if __name__ == "__main__":
    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()