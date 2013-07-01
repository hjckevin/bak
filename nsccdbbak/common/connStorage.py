# -*-coding:utf-8 -*-

'''
Created on 2013-2-18

@author: Administrator

本文件主要定了针对Swift存储平台的各项操作，包括查看存储文件信息，上传下载存储文件等。

'''

import os
import sys


from keystoneclient.v2_0 import client
from swiftclient import Connection, ClientException, HTTPException

try:
	from simplejson import loads as json_loads
except ImportError:
	from json import loads as json_loads
from hashlib import md5

class ConnStorage(object):
	'''
	classdocs
	'''

	def __init__(self, conf):
		'''
		根据配置文件初始化连接Swift云存储的客户端，包括认证系统和存储系统。
		'''
		self.conf = conf
		colon = conf['storuser'].find(":")
		if colon > 0 :
			self.user = conf['storuser'][:colon]
			self.tenant = conf['storuser'][colon+1:] 
		else:
			self.user = self.tenant = conf['storuser']
		print self.user, self.tenant
		self.pawd = conf['storpass']
		self.authurl = "http://" + conf['storip'] + ":" + conf['storport'] + "/v2.0/"
		
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
			try:
				self.swift.put_container(container)
			except ClientException, err:
				msg = ' '.join(str(x) for x in (err.http_status, err.http_reason))
				if err.http_response_content:
					if msg:
						msg += ': '
					msg += err.http_response_content[:60]
				print 'Error trying to create container %r: %s' % (container, msg)
			except Exception, err:
				print 'Error trying to create container %r: %s' % (container, err)
			
		obj = os.path.basename(objpath)
		fp = open(objpath, 'rb')
		self.swift.put_object(container, obj, fp)
	
	def head_container(self, conname):
		return self.swift.head_container(conname)
		
	
	def head_object(self, conname, objname):
		return self.swift.head_object(conname, objname)
	
	def download_object(self, conname, objname, dest_path):
		try:
			print "getting the %s/%s" %(conname, objname)
			headers, body = self.swift.get_object(conname, objname, resp_chunk_size=65536)
			print headers, body
			content_type = headers.get('content-type')
			if 'content-type' in headers:
				content_length = int(headers.get('content-length'))
			else:
				content_length = None
			etag = headers.get('etag')
			path = os.path.join(dest_path, objname) or objname
			if path[:1] in ('/', '\\'):
				path = path[1:]    
			md5sum = None
			if content_type.split(';', 1)[0] == 'text/directory':
				read_length = 0
				if 'x-object-manifest' not in headers:
					md5sum = md5()
				for chunk in body:
					read_length += len(chunk)
					if md5sum:
						md5sum.update(chunk)
			else:
				dirpath = os.path.dirname(path)
				fp = open(path, 'wb')
				read_length = 0
				if 'x-object-manifest' not in headers:
					md5sum = md5()
				for chunk in body:
					fp.write(chunk)
					read_length += len(chunk)
					if md5sum:
						md5sum.update(chunk)
				fp.close()
				
			if md5sum and md5sum.hexdigest() != etag:
				print '%s: md5sum != etag, %s != %s' %(path, md5sum.hexdigest(), etag)
			if content_length is not None and read_length != content_length:
				print '%s: read_length != content_length, %d != %d' %(path, read_length, content_length)   
			
		except ClientException, err:
			if err.http_status != 404:
				raise
			print 'Object %s not found' % repr('%s/%s' % (conname, objname))
	
#    def download_container(self, conname, dest_path):
#        
#        pass
	
	def delete_container(self, conname):
		self.swift.delete_container(conname)
		
	def delete_object(self, conname, objname):
		self.swift.delete_object(conname, objname)
		pass
	
if __name__ == '__main__':
	conf = {'storip':'172.31.201.116', 'storport':'5000', 
			'storuser':'demotest:demotest', 'storpass':'admin'}
	con = ConnStorage(conf)
	
	tenantlist = con.getTenantList()
	userlist = con.getUserList()
	print tenantlist
	print userlist

#    conlist = con.getContainerList()
#    for conName in conlist:
#        print conName
#        objlist = con.getObjectList(conName)
#        print objlist 
#    
	headers = con.head_container('swiftclient')
	print headers
	print headers.get('x-container-object-count')
	dict_tmp = {}
	