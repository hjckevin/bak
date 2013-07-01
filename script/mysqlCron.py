#!/usr/bin/env python
# -*-coding:utf-8 -*-

'''
Created on 2013-3-29

@author: Administrator

This script completes the global and increase backup automatically according to the backup plocy file.

'''


import os
import sys
import time
import gio
import gobject

from apscheduler.scheduler import Scheduler

import nsccdbbak
from nsccdbbak.common.configFilePraser import ConfigFilePraser
from nsccdbbak.common.connDatabase import ConnDatabase
from nsccdbbak.common.connStorage import ConnStorage

class bakCron(object):
    
    def __init__(self):
        self.sched = Scheduler()
        self.sched.daemonic = False
        self.sched.start()   
        
        self.assign_jobs()           
        self.assign_monitor()   
        
    def get_filepath(self):
        ''' 
        获取配置文件的路径，此路径在软件安装时指定目录。
        '''
        policyfile = os.path.dirname(nsccdbbak.__file__) + "/conf/Policy.conf"
        serverfile = os.path.dirname(nsccdbbak.__file__) + "/conf/Server.conf"

        return policyfile, serverfile
    
    def assign_jobs(self):
        '''
        读取配置文件，获得针对不同数据库的备份策略，设定备份线程。
        '''
        (policyfile, serverfile) = self.get_filepath()

        policyconfig = ConfigFilePraser(policyfile)       
        policys = policyconfig.load(13)
        print policys
        serverconfig = ConfigFilePraser(serverfile)
        servers = serverconfig.load(10)
        
        for dictTmp in policys:
            if dictTmp['flag'][0] == '1':
                for dict in servers:
                    if dict['server'][0] == dictTmp['server'][0]:
                        serverInfo = dict 
                for key in dictTmp.keys():
                    if dictTmp[key][0] == '':
                        dictTmp[key][0] = None
                glob_bak_name = 'glob_bak_' + dictTmp['server'][0]
                print [serverInfo, dictTmp['bakcon'][0]]
                self.sched.add_cron_job(self.glob_bak, args = [serverInfo, dictTmp['bakcon'][0]], month=dictTmp['globmonth'][0], day=dictTmp['globday'][0], 
                                         day_of_week=dictTmp['globweekday'][0], hour=dictTmp['globhour'][0], 
                                         minute=dictTmp['globminute'][0], second = '*/3', 
                                         name=glob_bak_name)
                incr_bak_name = 'incr_bak_' + dictTmp['server'][0]
                self.sched.add_cron_job(self.incr_bak, month=dictTmp['incmonth'][0], day=dictTmp['incday'][0], 
                                         day_of_week=dictTmp['incweekday'][0], hour=dictTmp['inchour'][0], 
                                         minute=dictTmp['incminute'][0], name=incr_bak_name)
        print self.sched.get_jobs()
        print 'assign jobs finished!'        
                   
    def assign_monitor(self):
        '''
        设定文件监控线程。
        '''
        self.sched.add_interval_job(self.monitorfile, name = 'monitorDaemon')
        print self.sched.get_jobs()
        print 'assign monitor finished'
    
    def filechange(self, monitor, file1, file2, evt_type):
        '''
        备份策略文件发生变化时，撤销计划列表中除文件监控以外的所有计划，然后重新设定备份线程。
        '''
        if evt_type == gio.FILE_MONITOR_EVENT_CHANGED: 
            print 'file changed'              
            for job in self.sched.get_jobs():
                print job
                if job.name != 'monitorDaemon':
                    self.sched.unschedule_job(job)
            
            self.assign_jobs()
   
    def monitorfile(self):   
        '''
        启动文件监控线程，并设定多线程运行环境。
        '''      
        gfile = gio.File(self.filepath)
        monitor = gfile.monitor_file(gio.FILE_MONITOR_NONE, None)
        monitor.connect("changed", self.filechange)   
        gobject.threads_init()     
        gml = gobject.MainLoop()
        gml.run() 
           
    def glob_bak(self, serConf, bakcontainer):
        '''
        负责执行一次全局备份，将备份文件上传至云存储。
        '''
        timestr = time.strftime(r"%Y-%m-%d_%H-%M-%S", time.localtime())
        print timestr
        conndb = ConnDatabase(serConf)
        connStor = ConnStorage(serConf)
        (result, bakfilepath) = conndb.conn.glob_bak()
        if result:
            connStor.upload_file(bakcontainer, bakfilepath)
        else:
            print 'global backup error!'
    
    def incr_bak(self, serConf, bakcontainer):
        '''
        负责执行一次增量备份，将备份文件上传至云存储。
        '''
        conndb = ConnDatabase(serConf)
        connStor = ConnStorage(serConf)
        (result, bakfilepath) = conndb.conn.incr_bak()
        if result:
            connStor.upload_file(bakcontainer, bakfilepath)
        else:
            print 'increase backup error!'


if __name__ == '__main__':    
    baktest = bakCron()
