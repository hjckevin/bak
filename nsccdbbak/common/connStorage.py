# -*-coding:utf-8 -*-

'''
Created on 2013-2-18

@author: Administrator
'''

import os

from keystoneclient.v2_0 import client
from swiftclient import Connection, ClientException, HTTPException

try:
    from simplejson import loads as json_loads
except ImportError:
    from json import loads as json_loads

class ConnStorage(object):
    '''
    classdocs
    '''

    def __init__(self, conf):
        '''
        根据配置文件初始化连接Swift云存储的客户端，包括认证系统和存储系统。
        '''
        self.conf = conf
        colon = conf['storuser'][0].find(":")
        if colon > 0 :
            self.user = conf['storuser'][0][:colon]
            self.tenant = conf['storuser'][0][colon+1:] 
        else:
            self.user = conf['storuser'][0]
            self.tenant = conf['storuser'][0]
        self.pawd = conf['storpass'][0] 
        self.authurl = "http://" + conf['storip'][0] + ":" + conf['storport'][0] + "/v2.0/"
        
        self.keystone = client.Client(username="admin", password="admin",
                                    tenant_name="admin", auth_url=self.authurl)        
        self.swift = Connection(authurl=self.authurl, user=self.user, key=self.pawd, 
                                auth_version="2", tenant_name=self.tenant, insecure = True)
        
    def getTenantList(self):
        items = self.keystone.tenants.list()
        tenantlist=[]
        for item in items:
            tenantlist.append(item.name)            
        return tenantlist
    
    def getUserList(self):
        items = self.keystone.users.list()
        userlist = []
        for item in items:
            userlist.append(item.name)
        return userlist
    
    def addTenant(self):
        tenantlist = self.getTenantList()
        if self.tenant not in tenantlist:
            self.keystone.tenants.create(tenant_name = self.tenant)
        else:
            print "The tenant \"%s\" already existed!" % self.tenant
    
    def addUser(self):
        tenantlist = self.keystone.tenants.list()
        my_tenant = [x for x in tenantlist if x.name == self.tenant][0]
        
        userlist = self.getUserList()
        if self.user not in userlist:
            self.keystone.users.create(name = self.tenant, password = self.pawd, 
                                       tenant_id = my_tenant.id)
        else:
            print "The user \"%s\" already existed under tenant \"%s\"!" % (self.tenant, self.user) 
    
    def getContainerList(self):
        items = self.swift.get_account()[1]
        conlist=[]
        for item in items:
            conlist.append(item.get('name', item.get('hjc')))
            
        return conlist
    
    def getObjectList(self,conName):
        items = self.swift.get_container(container=conName)[1]
        objlist = []
        for item in items:
            objlist.append(item.get('name', item.get('hjc')))
        
        return objlist
    
    def upload_file(self, container, objpath):
        conlist = self.getContainerList()
        if container not in conlist:
            self.swift.put_container(container)
            
        obj = os.path.basename(objpath)
        fp = open(objpath, 'rb')
        self.swift.put_object(container, obj, fp)
    
    def head_container(self, conname):
        self.swift.head_container(conname)
        pass
    
    def head_object(self, conname, objname):
        self.swift.head_object(conname, objname)
        pass
    
    def download_object(self, conname, objname):
        pass
    
    def delete_container(self, conname):
        self.swift.delete_container(conname)
        
    def delete_object(self, conname, objname):
        self.swift.delete_object(conname, objname)
        pass
    
if __name__ == '__main__':
    conf = {'storip':['172.31.201.116'], 'storport':['5000'], 
            'storuser':['demo:demo'], 'storpass':['admin']}
    con = ConnStorage(conf)
    
#    tenantlist = con.getTenantList()
#    userlist = con.getUserList()
#    print tenantlist
#    print userlist

#    conlist = con.getContainerList()
#    for conName in conlist:
#        print conName
#        objlist = con.getObjectList(conName)
#        print objlist 
#    
    con.addTenant()
    con.addUser()
    
        

        