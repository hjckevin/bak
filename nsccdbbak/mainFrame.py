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
import MySQLdb

from nsccdbbak.common.configFilePraser import ConfigFilePraser
from nsccdbbak.common.connDatabase import ConnDatabase
from nsccdbbak.common.connStorage import ConnStorage
from nsccdbbak.common import platform


class MainFrame(object):
    '''
    定义主窗口类
    '''
    def __init__(self):
        '''
        主窗口初始化，大多数的窗口元素都从glade文件中获取，少数在运行态定义；
        同时加载了程序所需的配置文件，包括服务器配置文件和备份策略配置文件。
        '''
        self.path = self.get_path()
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.path + '/glade/mainFrame.glade')
        self.mainFrame = self.builder.get_object('mainFrame')
        self.builder.connect_signals(self)

        self.serverTree = self.builder.get_object('treeviewSer')
        self.dbTable = self.builder.get_object('treeviewDatabase')
        self.storTable = self.builder.get_object('treeviewStorage')
        self.notebookR = self.builder.get_object('notebookRight')
        self.statusbar = self.builder.get_object('statusbar')
        
        self.frameNewServer = self.builder.get_object('frameNewServer')
        self.warnDial = self.builder.get_object('messagedialog')
        
        self.dialogDeleteStor = self.builder.get_object('dialogDeleteStor')
        self.dialogDeleteServer = self.builder.get_object('dialogDeleteServer')
        self.dialogRecover = self.builder.get_object('dialogRecover')
        self.dialogFile = self.builder.get_object('filechooserdialogDownload')
        
        self.radioGlob = self.builder.get_object('radiobuttonGlob')
        self.radioIncr = self.builder.get_object('radiobuttonIncr')
        self.radioGlob.set_active(gtk.FALSE)
        self.radioIncr.set_active(False)
        print self.radioGlob.get_active()
        
        self.popMemuServer = self.popMenuServerInit()  
        self.popMemuStor = self.popMemuStorInit()     
        
        
        self.PolicyConfig = ConfigFilePraser('conf/Policy.conf')
        self.loadServersInfo()

        self.serInfo = {}
        self.storInfo = {}
        
        self.mainFrame.show()                       
        self.serverTreeDisplay()
        
    def loadServersInfo(self):
        self.servers = []
        print self.servers
        self.ServerConfig = ConfigFilePraser('conf/Server.conf')
        self.servers = self.ServerConfig.load(10)
        print self.servers
        for dictTmp in self.servers:
            for key, value in dictTmp.iteritems():
                print key, value
                if 'pass' in key:
                    dictTmp[key][0] = base64.decodestring(value[0])

    def get_path(self):
        path = os.getcwd()
        return path
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
        self.comboboxDatabase.add_attribute(cell, 'text', 1)
        self.comboboxDatabase.set_active(0)
        
        self.frameNewServer.set_title("新建数据库")
        self.frameNewServer.show()
        
    def on_gtk_newServer(self, object, data=None):
        '''
        新建服务器
        '''
        self.newServerInit()
        self.dataBaseType = None                   
 
    def on_combobox1_changed(self, widget, data=None):
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
        servernames = []
        for dictTmp in self.servers:
            servernames.append(dictTmp['server'][0])
       
        if '' in self.serInfo.values():
            self.warnDial.set_markup('错误！请完整填写服务器和存储信息！')
            self.response = self.warnDial.run()
            self.warnDial.hide()
        else:
            self.ServerConfig.save(self.serInfo)
            self.loadServersInfo()
            self.serverTreeDisplay()
        
        self.frameNewServer.hide()
        
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
        else:
            pass
        
        if self.serverTree.get_model() == None:
            treeStore = gtk.TreeStore(str)
        else:
            treeStore = self.serverTree.get_model()
            treeStore.clear()
        
        try:
            print self.servers
            for dictTmp in self.servers:
                item = treeStore.append(None, dictTmp['server'])
                sortdict = sorted(dictTmp.iteritems(), key=lambda d:d[0])
                for i in xrange(len(sortdict)):
                    key = sortdict[i]
                    if key[0] != 'server':
                        value = key[0] + " : [" + key[1][0] + "]"                
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
            if self.serInfo['dbtype'][0] == 'MySQL':
                self.comboboxDatabase.set_active(1)
            elif self.serInfo['dbtype'][0] == 'Oracle':
                self.comboboxDatabase.set_active(2)
            else:
                self.comboboxDatabase.set_active(0)
            
            self.builder.get_object('entrySerName').set_text(self.serInfo['server'][0])
            self.builder.get_object('entrySerIP').set_text(self.serInfo['serip'][0])
            self.builder.get_object('entrySerPort').set_text(self.serInfo['serport'][0])
            self.builder.get_object('entrySerUser').set_text(self.serInfo['seruser'][0])
            self.builder.get_object('entrySerPass').set_text(self.serInfo['serpass'][0])
            self.builder.get_object('entryStorIP').set_text(self.serInfo['storip'][0])
            self.builder.get_object('entryStorPort').set_text(self.serInfo['storport'][0])
            self.builder.get_object('entryStorUser').set_text(self.serInfo['storuser'][0])
            self.builder.get_object('entryStorPass').set_text(self.serInfo['storpass'][0])
            
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
        
        conndb = ConnDatabase(self.serInfo)
        connStor = ConnStorage(self.serInfo)
        (result, bakfilepath) = conndb.conn.bk_now()
        if result:
            dial = self.builder.get_object('dialogContainer')
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
    def serverTree_buttonPress(self, widgt, event):
        '''
        选中服务器，弹出操作菜单。
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
                    if dictTmp['server'][0] == parent:
#                        for key, value in dictTmp.iteritems():
#                            print key, value
#                            if 'pass' in key:
#                                dictTmp[key][0] = base64.decodestring(value[0])
                        self.serInfo = dictTmp
            else:
                for dictTmp in self.servers:                            
                    if dictTmp['server'][0] == item:
#                        for key, value in dictTmp.iteritems():
#                            if 'pass' in key:
#                                dictTmp[key][0] = base64.decodestring(value[0])
                        self.serInfo = dictTmp
                       
            if event.button == 3:            
                self.popMemuServer.popup(None, None, None, event.button, event.time)
         
    def bkPolicy(self, object, data=None):
        '''
        配置备份策略，显示服务器原有备份策略。
        '''
        self.notebookR.set_current_page(2)
        
        policys = self.PolicyConfig.load(13)
        for dictTmp in policys:
            if dictTmp['server'] == self.serInfo['server']:
                self.builder.get_object('entryBakContainer').set_text(dictTmp['bakcon'][0])
                self.builder.get_object('entryGlobMonth').set_text(dictTmp['globmonth'][0])
                self.builder.get_object('entryGlobDay').set_text(dictTmp['globday'][0])
                self.builder.get_object('entryGlobWeekDay').set_text(dictTmp['globweekday'][0])
                self.builder.get_object('entryGlobHour').set_text(dictTmp['globhour'][0])
                self.builder.get_object('entryGlobMinute').set_text(dictTmp['globminute'][0])
                self.builder.get_object('entryIncMonth').set_text(dictTmp['incmonth'][0])
                self.builder.get_object('entryIncDay').set_text(dictTmp['incday'][0])
                self.builder.get_object('entryIncWeekDay').set_text(dictTmp['incweekday'][0])
                self.builder.get_object('entryIncHour').set_text(dictTmp['inchour'][0])
                self.builder.get_object('entryIncMinute').set_text(dictTmp['incminute'][0])
                if dictTmp['flag'][0] == '1':
                    self.builder.get_object('label41').set_text('正在运行')
                elif dictTmp['flag'][0] == '0':
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
        
        self.PolicyConfig.save(policyInfo)            
        
    def on_buttonApplyPolicy_clicked(self, object, data=None):
        '''
        保存修改的备份策略，写入配置文件，若为初次执行，则添加备份脚本到系统自启动程序目录，然后运行该备份策略。
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
        self.PolicyConfig.save(policyInfo)
        self.bkPolicy(object, data)    
            
    def addServiceRun(self):
        '''
        检查备份脚本是否为自启动服务，如果不是需要添加到系统自启动服务。
        '''
        if platform.is_windows():
            scriptdir = 'C:\\Users\\Administrator\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\'
            copy = 'copy '
        elif platform.is_linux():
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
  
    def popMemuStorInit(self):
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
        print self.serInfo
        connStor = ConnStorage(self.serInfo)
        if self.storInfo['objname'] == None:
            connStor.head_container(self.storInfo['conname'])
        else:
            connStor.head_object(self.storInfo['conname'], self.storInfo['objname'])
        pass
    def downloadStor(self, widgt, event):
        self.entryFileName = self.builder.get_object('entryFileName')
        if self.storInfo['objname'] != None:
            self.entryFileName.set_text(self.storInfo['objname'])
            self.response = self.dialogFile.run()
        else:
#            self.entryFileName.set_text(self.storInfo['conname'])
            pass
        pass
    def on_buttonSaveObj_clicked(self, object, data=None):
        connStor = ConnStorage(self.serInfo)
        dest_path = self.dialogFile.get_current_folder()
        if self.storInfo['objname'] == None:
#            connStor.download_container(self.storInfo['conname'], dest_path)
            pass
        else:
            connStor.download_object(self.storInfo['conname'], self.storInfo['objname'], dest_path)
        print dest_path
        self.dialogFile.hide()
        pass
    def on_buttonCancelObj_clicked(self, object, data=None):
        self.dialogFile.hide()
        pass
    def deleteStor(self, widgt, event):
        self.response = self.dialogDeleteStor.run()
        self.dialogDeleteStor.hide()    
        pass
    def on_buttonDelStor1_clicked(self, object, data=None):
        connStor = ConnStorage(self.serInfo)
        if self.storInfo['objname'] == None:
            connStor.delete_container(self.storInfo['conname'])
        else:
            connStor.delete_object(self.storInfo['conname'], self.storInfo['objname'])
        
        self.connStorage(object, data)
        pass
    def on_buttonDelStor2_clicked(self, object, data=None):
        self.dialogDeleteStor.hide()
        pass
    
    def recoverStor(self, widgt, event):
        if self.storInfo['objname'] == None:
            self.warnDial.set_markup("错误！请选择一个备份文件。")
            self.response = self.warnDial.run()
            self.warnDial.hide()
        else:
            self.response = self.dialogRecover.run()
            self.dialogRecover.hide()
        pass
    def on_buttonRecover1_clicked(self, object, data=None):
        conndb = ConnDatabase(self.serInfo)
        connstor = ConnStorage(self.serInfo)
		if self.storInfo['objname'] != None:
			connstor.download_object(self.storInfo['conname'], self.storInfo['objname'], conndb.conn.bkdir)
			conndb.conn.recover(conndb.conn.bkdir + "/" + self.storInfo['objname'])
        pass
    def on_buttonRecover2_clicked(self, object, data=None):
        self.dialogRecover.hide()
        pass
    def storTree_buttonPress(self, widgt, event):
        treeSelect = self.storTable.get_selection()
        treeSelect.set_mode(gtk.SELECTION_SINGLE)
        (treeStore, iter) = treeSelect.get_selected()
            
        if iter != None:
            item = treeStore.get_value(iter, 0)
            iterparent = treeStore.iter_parent(iter)
            if type(iterparent) == type(iter):
                parent = treeStore.get_value(iterparent, 0)
                self.storInfo = {'conname': parent, 'objname':item} 
            else:
                self.storInfo = {'conname':item, 'objname':None} 
            if event.button == 3:
                self.popMemuStor.popup(None, None, None, event.button, event.time)
    
if __name__ == '__main__':
    MainFrame()
    gtk.main()
    
