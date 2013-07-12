#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
Created on 2013-1-9

@author: hanjc
@email: hanjc@nscc-tj.gov.cn

本文件是整个软件系统的核心，提供了软件的入口和主界面，所有的功能的实现均在主界面上操作完成。

'''

try:
	import pygtk
	pygtk.require('2.0')
except:
	pass 
import sys
try:
	import gtk
except:
	print('GTK not available')
	sys.exit(1)
	
import os
import base64
import ConfigParser
import MySQLdb

from nsccdbbak.common.connDatabase import ConnDatabase
from nsccdbbak.common.connStorage import ConnStorage
from nsccdbbak.common import utils


class MainFrame(object):
	'''
	定义主窗口类
	'''
	lineNum = 0
	parse_exc = utils.ParseError
	
	def __init__(self):
		'''
		主窗口初始化，大多数的窗口元素都从glade文件中获取，少数在运行态定义；
		同时加载了程序所需的配置文件，包括服务器配置文件和备份策略配置文件。
		'''
		self.path = self.get_path()
		self.builder = gtk.Builder()
		print self.path
		self.builder.add_from_file(self.path + '/glade/mainFrame.glade')
		self.mainFrame = self.builder.get_object('mainFrame')
		self.builder.connect_signals(self)

		self.serverTree = self.builder.get_object('treeviewSer') # 服务器列表树形结构
		self.dbTable = self.builder.get_object('treeviewDatabase') # 数据库内容树形结构
		self.storTable = self.builder.get_object('treeviewStorage') # 云存储内容树形结构
		self.notebookR = self.builder.get_object('notebookRight') # 主窗口右侧数据库、云存储、备份策略标签页
		self.notebookPolicy = self.builder.get_object('notebookPolicy') # 备份策略标签页下全局和增量标签
		self.statusbar = self.builder.get_object('statusbar') # 主窗口底边状态栏
		
		self.frameNewServer = self.builder.get_object('frameNewServer') # 新建、修改服务器信息子窗口
		self.warnDial = self.builder.get_object('messagedialog') # 警告信息子窗口
		
		self.dialogDeleteStor = self.builder.get_object('dialogDeleteStor') # 删除云存储确认窗口
		self.dialogDeleteServer = self.builder.get_object('dialogDeleteServer') # 删除服务器信息确认窗口
		self.dialogRecover = self.builder.get_object('dialogRecover') # 云存储备份文件恢复到数据库确认窗口
		self.dialogFile = self.builder.get_object('filechooserdialogDownload') # 指定文件下载路径窗口

		self.popMemuServer = self.popMenuServerInit()  # 服务器列表右键弹出菜单
		self.popMemuStor = self.popMemuStorInit()     # 云存储右键弹出菜单
		
		self.loadServersInfo()
		self.loadPolicyInfo()

		self.serInfo = {}
		self.storInfo = {}
		
		self.mainFrame.show()                       
		self.serverTreeDisplay()
		
	def get_path(self):
		path = os.path.dirname(os.path.abspath(__file__))
		return path
	
	def loadServersInfo(self):
		'''
		读取服务器配置文件，把所有服务器信息保存到列表中。
		'''
		self.servers = []
		self.ServerConfig = ConfigParser.ConfigParser(allow_no_value=True)
		self.ServerConfig.read(self.path + '/conf/Server.conf')
		
		for section in self.ServerConfig.sections():
			dictTmp = {}
			colon = section.find(':')
			key, value = section[:colon], section[colon + 1:]
			dictTmp[key] = value
			for key, value in self.ServerConfig.items(section):
				if 'pass' in key:
					dictTmp[key] = base64.decodestring(value)
				else:
					dictTmp[key] = value
					
			self.servers.append(dictTmp.copy())
			dictTmp.clear()

	def saveServersInfo(self, serverInfo):
		'''
		保存服务器配置文件，把输入服务器信息（一节）保存到文件中。
		参数：serverInfo为服务器信息字典
		'''
		if 'server' in serverInfo.keys():
			sec = 'server' + ":" + serverInfo['server']
			try:
				if sec not in self.ServerConfig.sections():
					self.ServerConfig.add_section(sec)    
				for key in serverInfo.keys():
					if key != 'server':
						self.ServerConfig.set(sec, key, serverInfo[key])
			except:
				raise self.parse_exc('Repeated section', self.lineNum)                
		else:
			raise self.parse_exc('Invalid section', self.lineNum)
			
		
		with open(self.path + '/conf/Server.conf', 'wb') as configfile:
			self.ServerConfig.write(configfile)
				
	def loadPolicyInfo(self):		
		self.policys = []
		self.PolicyConfig = ConfigParser.ConfigParser(allow_no_value=True)
		self.PolicyConfig.read(self.path + '/conf/Policy.conf')	
		
		for section in self.PolicyConfig.sections():
			dictTmp = {}
			colon = section.find(':')
			key, value = section[:colon], section[colon + 1:]
			dictTmp[key] = value
			for key, value in self.PolicyConfig.items(section):
				if 'pass' in key:
					dictTmp[key] = base64.decodestring(value)
				else:
					dictTmp[key] = value
					
			self.policys.append(dictTmp.copy())
			dictTmp.clear()
	
	def savePolicyInfo(self, policyInfo):
		if 'server' in policyInfo.keys():
			sec = 'server' + ":" + policyInfo['server']
			try:
				if sec not in self.PolicyConfig.sections():
					self.PolicyConfig.add_section(sec)    
				for key in policyInfo.keys():
					if key != 'server':
						self.PolicyConfig.set(sec, key, policyInfo[key])
			except:
				raise self.parse_exc('Repeated section', self.lineNum)                
		else:
			raise self.parse_exc('Invalid section', self.lineNum)
			
		
		with open(self.path + '/conf/Policy.conf', 'wb') as configfile:
			self.PolicyConfig.write(configfile)
	
	def on_aboutDial_activate(self, menuitem, data=None):
		'''
		显示程序的帮助和关于信息。
		'''
		self.aboutDial = self.builder.get_object('aboutDialog')
		self.response = self.aboutDial.run()
		self.aboutDial.hide()
		
	def on_mainFrame_destroy(self, object, data=None):
		'''
		退出主程序窗口。
		'''
		gtk.main_quit()
	
	def on_display_db(self, object, data=None):
		self.notebookR.set_current_page(0)
		print 'dislpay db tree'
		
	def on_display_stor(self, object, data=None):
		self.notebookR.set_current_page(1)
		print 'dislpay stor tree'
		
	def on_display_policy(self, object, data=None):
		self.notebookR.set_current_page(2)
		self.notebookPolicy.set_current_page(0)
		self.on_radiobuttonOnce_toggled(object, data)
		print 'display policy'
		
	def newServerInit(self):
		'''
		初始化新建数据库窗口。
		'''
		self.comboboxDatabase = self.builder.get_object('comboDatabase') 
		if self.comboboxDatabase.get_model() == None:                
			liststore = gtk.ListStore(int, str) 
			liststore.append([0, "选择数据库类型: "])
			liststore.append([1, "MySQL"])
			liststore.append([2, "Oracle"])        
			self.comboboxDatabase.set_model(liststore)
			
			cell = gtk.CellRendererText()
			self.comboboxDatabase.pack_start(cell, True)
			self.comboboxDatabase.add_attribute(cell, 'text', 0)
			self.comboboxDatabase.set_active(0)
		else:
			self.comboboxDatabase.set_active(0)
			
		self.builder.get_object('entrySerName').set_text('')
		self.builder.get_object('entrySerIP').set_text('')
		self.builder.get_object('entrySerPort').set_text('')
		self.builder.get_object('entrySerUser').set_text('')
		self.builder.get_object('entrySerPass').set_text('')
		self.builder.get_object('entryStorIP').set_text('')
		self.builder.get_object('entryStorPort').set_text('')
		self.builder.get_object('entryStorUser').set_text('')
		self.builder.get_object('entryStorPass').set_text('')  
		
		self.frameNewServer.set_title("新建数据库")
		self.frameNewServer.show()
		
	def on_gtk_newServer(self, object, data=None):
		'''
		新建服务器
		'''
		self.newServerInit()
		self.dataBaseType = None                   

	def on_comboboxDatabase_changed(self, widget, data=None):
		'''
		选择数据库类型
		'''
		index = widget.get_active()
		model = widget.get_model()
		self.dataBaseType = model[index][1]
		
	def on_buttonCancel_clicked(self, object, data=None):
		'''
		新建、修改服务器时取消操作。
		'''
		self.frameNewServer.hide()    
		
	def get_SerInfo(self):
		'''
		获取新建、修改服务器时用户输入的相关数据。
		'''
		DatabaseType = self.comboboxDatabase.get_active_text()
		SerName = self.builder.get_object('entrySerName').get_text()
		SerIp = self.builder.get_object('entrySerIP').get_text()
		SerPort = self.builder.get_object('entrySerPort').get_text()
		SerUser = self.builder.get_object('entrySerUser').get_text()
		SerPass = self.builder.get_object('entrySerPass').get_text()
		StorIp = self.builder.get_object('entryStorIP').get_text()
		StorPort = self.builder.get_object('entryStorPort').get_text()
		StorUser = self.builder.get_object('entryStorUser').get_text()
		StorPass = self.builder.get_object('entryStorPass').get_text()

		return {"server":SerName, "dbtype":DatabaseType, 
				"serip":SerIp, "serport":SerPort, 
				"seruser":SerUser, "serpass":base64.encodestring(SerPass).rstrip(),
				"storip":StorIp, "storport":StorPort, 
				"storuser":StorUser, "storpass":base64.encodestring(StorPass).rstrip()}
	
	def on_buttonSave_clicked(self, object, data=None):
		'''
		新建、修改服务器信息完成后保存到配置文件。
		'''
		self.serInfo = self.get_SerInfo()
	
		if '' in self.serInfo.values():
			self.warnDial.set_markup('错误！请完整填写服务器和存储信息！')
			self.response = self.warnDial.run()
			self.warnDial.hide()
		else:
			self.frameNewServer.hide()
			self.saveServersInfo(self.serInfo)
			self.loadServersInfo()
			self.serverTreeDisplay()
		
	def serverTreeDisplay(self):      
		'''
		根据配置文件显示服务器相关信息。
		'''         
		if len(self.serverTree.get_columns()) == 0:
			columnTree = gtk.TreeViewColumn()
			cell = gtk.CellRendererText()
			columnTree.pack_start(cell, True)
			columnTree.add_attribute(cell, "text", 0)
			self.serverTree.insert_column(columnTree, 0)
		
		if self.serverTree.get_model() == None:
			treeStore = gtk.TreeStore(str)
		else:
			treeStore = self.serverTree.get_model()
			treeStore.clear()
		
		try:
			for dictTmp in self.servers:
				item = treeStore.append(None, dictTmp['server'].split(','))
				sortdict = sorted(dictTmp.iteritems(), key=lambda d:d[0])
				for i in xrange(len(sortdict)):
					key = sortdict[i]
					if key[0] != 'server' or 'pass' not in key[0]:
						value = key[0] + " : [" + key[1] + "]"                
						treeStore.append(item, [value])     
					
		except IOError, e:
			errStr = 'Configure file load Error %d: %s' % (e.args[0], e.args[1])
			self.warnDial.set_markup(errStr)
			self.response = self.warnDial.run()
			self.warnDial.hide()
		
		self.serverTree.set_model(treeStore)

	def popMenuServerInit(self):
		'''
		初始化服务器列表中的弹出窗口，绑定触发事件。
		'''
		popMenu = gtk.Menu()
		
		ser_item = gtk.MenuItem("连接数据库")
		ser_item.connect_object("button-press-event", self.connServer, popMenu)
		ser_item.show()
		
		stor_item = gtk.MenuItem("连接云存储")
		stor_item.connect_object("button-press-event", self.connStorage, popMenu)
		stor_item.show()
		
		modify_item = gtk.MenuItem("修改服务器")
		modify_item.connect_object("button-press-event", self.modifyServer, popMenu) 
		modify_item.show()
		
		delete_item = gtk.MenuItem("删除服务器")
		delete_item.connect_object("button-press-event", self.deleteServer, popMenu)
		delete_item.show()
		
		backup_item = gtk.MenuItem("备份数据库")
		backup_item.connect_object("button-press-event", self.bkDatabase, popMenu)
		backup_item.show()
		
		bkstra_item = gtk.MenuItem("设定备份策略")
		bkstra_item.connect_object("button-press-event", self.bkPolicy, popMenu)
		bkstra_item.show()

		popMenu.append(ser_item)
		popMenu.append(stor_item)
		popMenu.append(modify_item)
		popMenu.append(delete_item)
		popMenu.append(backup_item)
		popMenu.append(bkstra_item)
	
		return popMenu
	def connServer(self, widgt, event):
		'''
		连接数据库，并根据返回数据显示到数据库信息列表。
		'''
		print "display the database content"
		self.popMemuServer.hide()
		conndb = ConnDatabase(self.serInfo)
		
		if len(self.dbTable.get_columns()) == 0:
			columnTree = gtk.TreeViewColumn()       
			cell = gtk.CellRendererText()
			columnTree.pack_start(cell, True)
			columnTree.add_attribute(cell, "text", 0)
			self.dbTable.insert_column(columnTree, 0)
		else:
			print self.dbTable.get_columns()
				
		if self.dbTable.get_model() == None:
			treeStore = gtk.TreeStore(str)
		else:
			treeStore = self.dbTable.get_model()
			treeStore.clear()

		try:
			dbs = conndb.get()
			for i in xrange(len(dbs)):
				item = treeStore.append(None, dbs[i][0])
				for j in xrange(len(dbs[i][1])):
					if j != 0:
						treeStore.append(item, dbs[i][1][j])
		except MySQLdb.Error, e:
			errStr = 'MySQL Error %d: %s' % (e.args[0], e.args[1])
			self.warnDial.set_markup(errStr)
			self.response = self.warnDial.run()
			self.warnDial.hide()
			
		self.dbTable.set_model(treeStore)        
		self.notebookR.set_current_page(0)
		
		self.statusbar.get_context_id('dbConnInfo')
		self.statusbar.push(0, "显示数据库表信息")   
	def connStorage(self, widgt, event):
		'''
		连接云存储，并根据返回数据显示到云存储信息列表。
		'''
		print "display the storage file"
		self.popMemuServer.hide()
		connStor = ConnStorage(self.serInfo)
		
		if len(self.storTable.get_columns()) == 0:
			columnTree = gtk.TreeViewColumn()       
			cell = gtk.CellRendererText()
			columnTree.pack_start(cell, True)
			columnTree.add_attribute(cell, "text", 0)
			self.storTable.insert_column(columnTree, 0)
		else:
			print self.storTable.get_columns()
				
		if self.storTable.get_model() == None:
			treeStore = gtk.TreeStore(str)
		else:
			treeStore = self.storTable.get_model()
			treeStore.clear()
		
		conList = connStor.getContainerList()
		for con in conList:
#            conName = []
#            conName.append(con)
			item = treeStore.append(None, [con])  # 这里的conName必须为列表
			objlist = connStor.getObjectList(con)
			for obj in objlist:
				treeStore.append(item, [obj])

		self.storTable.set_model(treeStore)
		self.notebookR.set_current_page(1)
		self.statusbar.get_context_id('storConnInfo')
		self.statusbar.push(0, "显示云存储内容")        
	def modifyServer(self, object, data=None):      
		'''
		修改服务器信息窗口，根据配置文件显示原有服务器信息。
		'''
		if len(self.serInfo.keys()) == 0:
			self.warnDial.set_markup('错误！请先选择服务器！')
			self.response = self.warnDial.run()
			self.warnDial.hide()
		else:        
			self.newServerInit() 
			if self.serInfo['dbtype'] == 'MySQL':
				self.comboboxDatabase.set_active(1)
			elif self.serInfo['dbtype'] == 'Oracle':
				self.comboboxDatabase.set_active(2)
			else:
				self.comboboxDatabase.set_active(0)
			
			self.builder.get_object('entrySerName').set_text(self.serInfo['server'])
			self.builder.get_object('entrySerIP').set_text(self.serInfo['serip'])
			self.builder.get_object('entrySerPort').set_text(self.serInfo['serport'])
			self.builder.get_object('entrySerUser').set_text(self.serInfo['seruser'])
			self.builder.get_object('entrySerPass').set_text(self.serInfo['serpass'])
			self.builder.get_object('entryStorIP').set_text(self.serInfo['storip'])
			self.builder.get_object('entryStorPort').set_text(self.serInfo['storport'])
			self.builder.get_object('entryStorUser').set_text(self.serInfo['storuser'])
			self.builder.get_object('entryStorPass').set_text(self.serInfo['storpass'])
			
			self.frameNewServer.set_title('修改服务器')
			self.frameNewServer.show_all()          
	def deleteServer(self, object, data=None):
		'''
		删除服务器相关信息，并写入配置文件。
		'''
		if len(self.serInfo.keys()) == 0:
			self.warnDial.set_markup('错误！请先选择服务器！')
			self.response = self.warnDial.run()
			self.warnDial.hide()
		else:
			self.response = self.dialogDeleteServer.run()
			self.dialogDeleteServer.hide()   
			
	def on_buttonDelServer1_clicked(self, object, data=None):
		self.ServerConfig.delete(self.serInfo)
		self.loadServersInfo()
		self.serverTreeDisplay()
		pass
	
	def on_buttonDelServer2_clicked(self, object, data=None):
		self.dialogDeleteServer.hide()
		pass
	
	def bkDatabase(self, widgt, event):
		'''
		即时备份操作，需要用户输入保存到的容器名。
		'''
		self.statusbar.get_context_id('backInfo')
		self.statusbar.push(0, "备份数据库")
		
		print self.serInfo
		conndb = ConnDatabase(self.serInfo)
		connStor = ConnStorage(self.serInfo)
		(result, bakfilepath) = conndb.conn.bk_now()
		if result:
			dial = self.builder.get_object('dialogContainerName')
			conName = self.builder.get_object('entryContainer')
			self.response = dial.run()
			dial.hide()
			if conName.get_text() != '':
				connStor.upload_file(conName.get_text(), bakfilepath)
				self.statusbar.get_context_id('backInfo')
				self.statusbar.push(0, "数据库备份成功")
			else:
				self.statusbar.get_context_id('backInfo')
				self.statusbar.push(0, "未能获取指定的容器名")
		else:
			self.statusbar.get_context_id('backInfo')
			self.statusbar.push(0, "数据库备份失败")
	
		self.connStorage(widgt, event)      
	
		
	def bkPolicy(self, object, data=None):
		'''
		配置备份策略，显示服务器原有备份策略。
		'''
		self.on_display_policy(object, data)
		
		for dictTmp in self.policys:
			if dictTmp['server'] == self.serInfo['server']:
				
				if dictTmp['flag'] == '1':
					self.builder.get_object('label41').set_text('正在运行')
				elif dictTmp['flag'] == '0':
					self.builder.get_object('label41').set_text('停止运行')
				else:
					self.builder.get_object('label41').set_text('无')
	
	def on_buttonResetPolicy_clicked(self, object, data=None): 
		'''
		重置配置策略，写入配置文件。
		'''       
		self.builder.get_object('entryBakContainer').set_text('')
		self.builder.get_object('entryGlobMonth').set_text('')
		self.builder.get_object('entryGlobDay').set_text('')
		self.builder.get_object('entryGlobWeekDay').set_text('')
		self.builder.get_object('entryGlobHour').set_text('')
		self.builder.get_object('entryGlobMinute').set_text('')
		self.builder.get_object('entryIncMonth').set_text('')
		self.builder.get_object('entryIncDay').set_text('')
		self.builder.get_object('entryIncWeekDay').set_text('')
		self.builder.get_object('entryIncHour').set_text('')
		self.builder.get_object('entryIncMinute').set_text('')
		self.builder.get_object('entryBakContainer').set_text('')
		
		policyInfo = {'server':self.serInfo['server'][0], 'bakcon':'', 'flag':0,
					'globmonth':'', 'globday':'',
					'globweekday':'', 'globhour':'', 'globminute':'',
					'incmonth':'', 'incday':'', 
					'incweekday':'', 'inchour':'','incminute':''}
		
		self.savePolicyInfo(policyInfo)            
		
	def on_buttonApplyPolicy_clicked(self, object, data=None):
		'''
		保存修改的备份策略，写入配置文件，若为初次执行，则添加备份脚本到系统
		自启动程序目录，然后运行该备份策略。
		'''
		globmonth = self.builder.get_object('entryGlobMonth').get_text()
		globday = self.builder.get_object('entryGlobDay').get_text()
		globweekday = self.builder.get_object('entryGlobWeekDay').get_text()
		globhour = self.builder.get_object('entryGlobHour').get_text()
		globminute = self.builder.get_object('entryGlobMinute').get_text()
		incmonth = self.builder.get_object('entryIncMonth').get_text()
		incday = self.builder.get_object('entryIncDay').get_text()
		incweekday = self.builder.get_object('entryIncWeekDay').get_text()
		inchour = self.builder.get_object('entryIncHour').get_text()
		incminute = self.builder.get_object('entryIncMinute').get_text()
		bakcontainer = self.builder.get_object('entryBakContainer').get_text()
		policyInfo = {'server':self.serInfo['server'][0], 'bakcon':bakcontainer, 'flag':'1',
					'globmonth':globmonth, 'globday':globday,
					'globweekday':globweekday, 'globhour':globhour, 'globminute':globminute,
					'incmonth':incmonth, 'incday':incday, 
					'incweekday':incweekday, 'inchour':inchour, 'incminute':incminute}        
		
		self.addServiceRun()
		self.savePolicyInfo(policyInfo)
		self.bkPolicy(object, data)    
			
	def addServiceRun(self):
		'''
		检查备份脚本是否为自启动服务，如果不是需要添加到系统自启动服务。
		'''
		if utils.is_windows():
			scriptdir = 'C:\\Users\\Administrator\\AppData\\Roaming\\Microsoft\\Windows \
						\\Start Menu\\Programs\\Startup\\'
			copy = 'copy '
		elif utils.is_linux():
			scriptdir = '/etc/init.d/'
			copy = 'cp '
		else:
			print 'Unkown System Type!'
			
		filelist = os.listdir(scriptdir)
		dbtype = self.serInfo['dbtype'][0]
		if dbtype == 'MySQL':
			bakscript = 'mysqlCron.py'
		elif dbtype == 'Oracle':
			bakscript = 'oracleCron.py'
		else:
			print "Unkown database type!"
			
		if bakscript not in filelist:
			print scriptdir
			os.system(copy + bakscript + ' "' + scriptdir + '"')
			os.system('python ' + '"' + scriptdir + bakscript + '"')

	def serverTree_buttonPress(self, widgt, event):
		'''
		选中服务器，弹出右键操作菜单。
		'''
		treeSelect = self.serverTree.get_selection()
		treeSelect.set_mode(gtk.SELECTION_SINGLE)
		(treeStore, iter) = treeSelect.get_selected()
		if iter != None:
			item = treeStore.get_value(iter, 0)
			iterparent = treeStore.iter_parent(iter)
			if type(iterparent) == type(iter):
				parent = treeStore.get_value(iterparent, 0)
				for dictTmp in self.servers:                            
					if dictTmp['server'] == parent:
						self.serInfo = dictTmp
			else:
				for dictTmp in self.servers:                            
					if dictTmp['server'] == item:
						self.serInfo = dictTmp
					
			if event.button == 3:            
				self.popMemuServer.popup(None, None, None, event.button, event.time)

	def popMemuStorInit(self):
		'''
		云存储右键弹出菜单
		'''
		popMenu = gtk.Menu()
		
		head_item = gtk.MenuItem("查看")
		head_item.connect_object("button-press-event", self.headStor, popMenu)
		head_item.show()
		
		download_item = gtk.MenuItem("下载")
		download_item.connect_object("button-press-event", self.downloadStor, popMenu)
		download_item.show() 
		
		delete_item = gtk.MenuItem("删除")
		delete_item.connect_object("button-press-event", self.deleteStor, popMenu)
		delete_item.show() 
		
		recover_item = gtk.MenuItem("恢复")
		recover_item.connect_object("button-press-event", self.recoverStor, popMenu)
		recover_item.show() 
		
		popMenu.append(head_item)
		popMenu.append(download_item)
		popMenu.append(delete_item)
		popMenu.append(recover_item)
		return popMenu
	def headStor(self, widgt, event):
		'''
		获取云存储容器或对象的详细信息
		'''
		print self.serInfo
		connStor = ConnStorage(self.serInfo)
		if self.storInfo['objname'] is None:
			info = connStor.head_container(self.storInfo['conname'])
		else:
			info = connStor.head_object(self.storInfo['conname'], self.storInfo['objname'])
		info_str = " "
		for key, value in info.items():
			info_str += key + " : " + str(value) + "\n"
		self.warnDial.set_markup(info_str)
		self.response = self.warnDial.run()
		self.warnDial.hide()
		
	def downloadStor(self, widgt, event):
		'''
		下载云存储中的对象，由用户选择存放位置
		'''
		self.entryFileName = self.builder.get_object('entryFileName')
		if self.storInfo['objname'] is None:
#            self.entryFileName.set_text(self.storInfo['conname'])
			pass
		else:
			self.entryFileName.set_text(self.storInfo['objname'])
			self.response = self.dialogFile.run()
	def on_buttonSaveObj_clicked(self, object, data=None):
		connStor = ConnStorage(self.serInfo)
		dest_path = self.dialogFile.get_current_folder()
		if self.storInfo['objname'] is None:
		# 不提供针对整个容器的下载
#            connStor.download_container(self.storInfo['conname'], dest_path)
			pass
		else:
			connStor.download_object(self.storInfo['conname'], self.storInfo['objname'], dest_path)
		self.dialogFile.hide()

	def on_buttonCancelObj_clicked(self, object, data=None):
		self.dialogFile.hide()
		
	def deleteStor(self, widgt, event):
		'''
		删除云存储中的容器或对象
		'''
		self.response = self.dialogDeleteStor.run()
		self.dialogDeleteStor.hide()    
	def on_buttonDelStor1_clicked(self, object, data=None):
		connStor = ConnStorage(self.serInfo)
		if self.storInfo['objname'] is None:
			connStor.delete_container(self.storInfo['conname'])
		else:
			connStor.delete_object(self.storInfo['conname'], self.storInfo['objname'])
		
		self.connStorage(object, data)
	def on_buttonDelStor2_clicked(self, object, data=None):
		self.dialogDeleteStor.hide()

	def recoverStor(self, widgt, event):
		'''
		将选定的云存储备份文件还原到数据库
		'''
		if self.storInfo['objname'] is None:
			self.warnDial.set_markup("错误！请选择一个备份文件。")
			self.response = self.warnDial.run()
			self.warnDial.hide()
		else:
			self.response = self.dialogRecover.run()
			self.dialogRecover.hide()

	def on_buttonRecover1_clicked(self, object, data=None):
		conndb = ConnDatabase(self.serInfo)
		connstor = ConnStorage(self.serInfo)
		if self.storInfo['objname'][0] is not None:
			if 'glob' in self.storInfo['objname'][0]:
			# 从全局备份恢复
				connstor.download_object(self.storInfo['conname'][0], 
										self.storInfo['objname'][0], 
										conndb.conn.bkdir)
				conndb.conn.recover_glob(conndb.conn.bkdir + "/" + self.storInfo['objname'][0])
			elif 'incr' in self.storInfo['objname'][0]:
			# 从增量备份恢复
				timestop = float(connstor.head_object(self.storInfo['conname'][0], \
							self.storInfo['objname'][0]).get('x-timestamp'))
				dict_tmp = {}
				objlist = connstor.getContainerList(self.storInfo['conname'][0])
				for objname in objlist:
					if 'glob' in objname:
					# 首先查找时间最近的一次全局备份
						timestamp = float(connstor.head_object(self.storInfo['conname'][0], \
									objname).get('x-timestamp'))
						dict_tmp[timestamp] = objname
				glob_bakfile = max(dict_tmp.itervalues(), key = lambda k:k)
				glob_timestamp = dict_tmp.keys()[dict_tmp.values().index(glob_bakfile)]
				dict_tmp.clear()
				for objname in objlist:
					if 'incr' in objname:
					# 然后查找该全局备份后所有的增量备份，到选中的增量备份为止
						timestamp = float(connstor.head_object(self.storInfo['conname'][0], \
									objname).get('x-timestamp'))
						if timestamp >= glob_timestamp and timestamp <= timestop:
							dict_tmp[timestamp] = objname
				# timestamp_list = sorted(dict_tmp.iterkeys(), key=lambda k:k[0])
				# incr_bakfile_list = []
				# for item in timestamp_list:
				# incr_bakfile_list.append(timestamp_list[item])
				incr_bakfile_list = sorted(dict_tmp.itervaluse(), key=lambda k:k[0])
				conndb.conn.recover_glob(glob_bakfile)
				conndb.conn.recover_incr(incr_bakfile_list)
			else:
				print 'Unkown backup file type!'
	def on_buttonRecover2_clicked(self, object, data=None):
		self.dialogRecover.hide()

	def storTree_buttonPress(self, widgt, event):
		'''
		在云存储显示列表中右键时，弹出菜单。
		'''
		treeSelect = self.storTable.get_selection()
		treeSelect.set_mode(gtk.SELECTION_SINGLE)
		(treeStore, iter) = treeSelect.get_selected()
		
		if iter is not None:
			item = treeStore.get_value(iter, 0)
			iterparent = treeStore.iter_parent(iter)
			if type(iterparent) == type(iter):
				parent = treeStore.get_value(iterparent, 0)
				self.storInfo = {'conname': parent, 'objname':item} 
			else:
				self.storInfo = {'conname':item, 'objname':None} 
			if event.button == 3:
				self.popMemuStor.popup(None, None, None, event.button, event.time)
	
	def on_radiobuttonOnce_toggled(self, object, data=None):
		self.builder.get_object('radiobuttonWeekday').hide()
		self.builder.get_object('radiobuttonDay').hide()
		self.builder.get_object('radiobuttonEvery').hide()
		
		self.builder.get_object('radiobuttonEveryDay').set_label("指定日期")
		self.builder.get_object('calendar').show()
		pass
	
	def on_radiobuttonRepeat_toggled(self, object, data=None):
		self.builder.get_object('radiobuttonWeekday').show()
		self.builder.get_object('radiobuttonDay').show()
		self.builder.get_object('radiobuttonEvery').show()
		
		self.builder.get_object('radiobuttonEveryDay').set_label("每天")
		self.builder.get_object('calendar').hide()
		pass
	
if __name__ == '__main__':
	MainFrame()
	gtk.main()
	
