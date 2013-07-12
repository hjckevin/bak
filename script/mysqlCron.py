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
import base64
import ConfigParser

from apscheduler.scheduler import Scheduler

import nsccdbbak

from nsccdbbak.common.connDatabase import ConnDatabase
from nsccdbbak.common.connStorage import ConnStorage

class bakCron(object):
	
	def __init__(self):
		self.sched = Scheduler()
		self.sched.daemonic = False
		self.sched.start()   
		
		self.assign_jobs()           
		self.assign_monitor()   
		
	def get_fileconfig(self):
		''' 
		获取配置文件的路径，此路径在软件安装时指定目录。
		'''
		policyfile = os.path.dirname(nsccdbbak.__file__) + "/conf/Policy.conf"
		serverfile = os.path.dirname(nsccdbbak.__file__) + "/conf/Server.conf"
		
		policys = []
		PolicyConfig = ConfigParser.ConfigParser(allow_no_value=True)
		PolicyConfig.read(policyfile)	
		
		for section in PolicyConfig.sections():
			dictTmp = {}
			colon = section.find(':')
			key, value = section[:colon], section[colon + 1:]
			dictTmp[key] = value
			for key, value in PolicyConfig.items(section):
				if 'pass' in key:
					dictTmp[key] = base64.decodestring(value)
				else:
					dictTmp[key] = value
					
			policys.append(dictTmp.copy())
			dictTmp.clear()
		
		servers = []
		ServerConfig = ConfigParser.ConfigParser(allow_no_value=True)
		ServerConfig.read(serverfile)
		
		for section in ServerConfig.sections():
			dictTmp = {}
			colon = section.find(':')
			key, value = section[:colon], section[colon + 1:]
			dictTmp[key] = value
			for key, value in ServerConfig.items(section):
				if 'pass' in key:
					dictTmp[key] = base64.decodestring(value)
				else:
					dictTmp[key] = value
					
			servers.append(dictTmp.copy())
			dictTmp.clear()

		return policys, servers
	
	def assign_jobs(self):
		'''
		读取配置文件，获得针对不同数据库的备份策略，设定备份线程。
		'''
		(policys, servers) = self.get_fileconfig()

		for dictTmp in policys:
			if dictTmp['flag'] == '1':
				for dict in servers:
					if dict['server'] == dictTmp['server']:
						serverInfo = dict 
				for key in dictTmp.keys():
					if dictTmp[key] == '':
						dictTmp[key] = None
				glob_bak_name = 'glob_bak_' + dictTmp['server']
				print [serverInfo, dictTmp['bakcon']]
				self.sched.add_cron_job(self.glob_bak, args = [serverInfo, dictTmp['bakcon']], month=dictTmp['globmonth'], day=dictTmp['globday'], 
										day_of_week=dictTmp['globweekday'], hour=dictTmp['globhour'], 
										minute=dictTmp['globminute'], second = '*/3', 
										name=glob_bak_name)
				incr_bak_name = 'incr_bak_' + dictTmp['server']
				self.sched.add_cron_job(self.incr_bak, month=dictTmp['incmonth'], day=dictTmp['incday'], 
										day_of_week=dictTmp['incweekday'], hour=dictTmp['inchour'], 
										minute=dictTmp['incminute'], name=incr_bak_name)
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
