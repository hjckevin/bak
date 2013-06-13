# -*-coding:utf-8 -*-
'''
Created on 2013-2-18

@author: Administrator
'''

import os
import sys
import time
import zipfile
import tarfile
import ConfigParser

from nsccdbbak.common import utils

try:
	import MySQLdb
except:
	print('MySQLdb not available')
	sys.exit(1)
	
try:
	import cx_Oracle
except:
	print('cx_Oracle not available')
	sys.exit(1)

class ConnMysql(object):
	'''
	classdocs
	'''
	def __init__(self, conf):
		'''
		Constructor
		'''
		if utils.is_windows():
			self.bkdir = os.environ['TMP']
		elif utils.is_linux():
			self.bkdir = '/var/tmp/mysqlbak'
		else:
			print 'Unkown System Type!'
			sys.exit(1)
		self.conf = conf
		self.dbs = {}
		self.conn = MySQLdb.connect(host=self.conf['serip'][0], 
									user=self.conf['seruser'][0], 
									passwd=self.conf['serpass'][0])
		self.logbinpath = self._get_logbin_path()
		
	def _get_logbin_path(self):
		if utils.is_windows():
			try:
				cursor = self.conn.cursor()
				cursor.execute("show variables like 'basedir'")
				basedir = cursor.fetchall()[0][1]
				inipath = basedir + 'my.ini'
				
			except MySQLdb.Error, e:
				print 'MySQL Error %d: %s' % (e.args[0], e.args[1])
		elif utils.is_linux():
			inipath = '/etc/mysql/my.cnf'
		else:
			print 'Unkown System Type!'
			sys.exit(1)
			
		config = ConfigParser.ConfigParser(allow_no_value=True)
		config.read(inipath)
		logbin_path = config.get('mysqld', 'log-bin')
		print logbin_path
		
		if not logbin_path:
			cursor = self.conn.cursor()
			cursor.execute("show variables like 'datadir'")
			datadir = cursor.fetchall()[0][1]
			cursor.close()
			if logbin_path != None:
				return datadir.strip('\"') + '/' + logbin_path
			else:
				return datadir.strip('\"') + '/' + utils.hostname() + '-bin'
		elif os.path.isabs(logbin_path):
			cursor.close()
			return logbin_path.strip('\"')
		
	def _get_logbin_last(self):
		logbin_index = os.path.dirname(self.logbinpath) + '/' + \
					os.path.basename(self.logbinpath).split('.')[0] + '.index'
		fp = open(logbin_index)
		logbin_filelist = fp.readlines()
		
		return logbin_filelist[len(logbin_filelist) - 2]
		
	def get_dbs(self):
		try:
			cursor = self.conn.cursor()
			cursor.execute('show databases')
			rows = cursor.fetchall()
			for dbname in rows:
				self.conn.select_db(dbname[0])
				cursor.execute('show tables')
				tables = cursor.fetchall()
				self.dbs[dbname] = tables;  
			cursor.close()
			return sorted(self.dbs.iteritems(), key=lambda d:d[0])
		except MySQLdb.Error, e:
			print 'MySQL Error %d: %s' % (e.args[0], e.args[1])
		raise
			
	def bk_now(self):
		if utils.is_windows():
			timestamp = str(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time())))
			dump_dir = self.bkdir + '\\' + timestamp
			dump_file = dump_dir + '\\' + timestamp + '_glob.sql'
			zip_file = timestamp + '_glob.zip'
			zip_file_path = dump_dir + '\\' + zip_file
			log_file = dump_dir + '\\' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' --all-databases '
			
			os.system('md ' + dump_dir)
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				myzipfile = zipfile.ZipFile(zip_file, 'w')
				myzipfile.write(dump_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
			pass
		elif utils.is_linux():
			timestamp = str(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time())))
			dump_dir = self.bkdir + '/' + timestamp
			dump_file = dump_dir + '/' + timestamp + '_glob.sql'
			gz_file = dump_dir + '/' + timestamp + '_glob.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' --all-databases '
			
			os.system('mkdir -p ' + dump_dir)
			os.system('chmod 777 -R ' + dump_dir)
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(dump_file)
				tarfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, gz_file
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		else:
			print 'Unkown System Type!'
			sys.exit(1)
	
	def glob_bak(self):
		timestamp = str(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time())))
		
		if utils.is_windows():
			dump_dir = self.bkdir + '\\' + timestamp
			dump_file = dump_dir + '\\' + timestamp + '_glob.sql'
			zip_file = timestamp + '_glob.zip'
			zip_file_path = dump_dir + '\\' + zip_file
			log_file = dump_dir + '\\' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' --all-databases --flush-logs --master-data=2'
			
			os.system('md ' + dump_dir)
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				myzipfile = zipfile.ZipFile(zip_file, 'w')
				myzipfile.write(dump_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
			pass
		elif utils.is_linux():
			dump_dir = self.bkdir + '/' + timestamp
			dump_file = dump_dir + '/' + timestamp + '_glob.sql'
			gz_file = dump_dir + '/' + timestamp + '_glob.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' --all-databases --flush-logs --master-data=2'
			
			os.system('mkdir -p ' + dump_dir)
			os.system('chmod 777 -R ' + dump_dir)
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(dump_file)
				tarfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, gz_file
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		else:
			print 'Unkown System Type!'
			sys.exit(1)
	
	def incr_bak(self, starttime, stoptime):
		timestamp = str(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(time.time())))
		
		if utils.is_windows():
			dump_dir = self.bkdir + '\\' + timestamp
			zip_file = timestamp + '_incr.zip'
			zip_file_path = dump_dir + '\\' + zip_file
			log_file = dump_dir + '\\' + timestamp + '_incr.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' flush-logs'
			
			os.system('md ' + dump_dir)
			if os.system('mysqladmin ' + options) == 0:
				logbin_file = self._get_logbin_last()
				myzipfile = zipfile.ZipFile(zip_file, 'w')
				myzipfile.write(logbin_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
			pass
		elif utils.is_linux():
			dump_dir = self.bkdir + '/' + timestamp
			tar_file = dump_dir + '/' + timestamp + '_incr.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_incr.log'
			options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
					+ ' -p' + self.conf['serpass'][0] + ' flush-logs'
			
			os.system('mkdir -p ' + dump_dir)
			os.system('chmod 777 -R ' + dump_dir)
			if os.system('mysqlbinlog ' + options) == 0:
				logbin_file = self._get_logbin_last()
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(logbin_file)
				tarfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, tar_file
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		else:
			print 'Unkown System Type!'
			sys.exit(1)
		pass    
	
	def recover(self, bakfile):
		pass
	
	def recover_glob(self, bakfile):
		options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
				+ ' -p' + self.conf['serpass'][0]
		
		if zipfile.is_zipfile(bakfile):
			file_obj = zipfile.ZipFile(bakfile)
			file_name = file_obj.namelist()[0]
			sql_file = open(self.bakdir + "\\" + file_name, 'wb')
			sql_file.write(file_obj.read(file_name))
			sql_file.close()
			os.system("mysql " + options + " < " + sql_file)           
		elif tarfile.is_tarfile(bakfile):
			tar_file = tarfile.open(bakfile, 'r|gz')
			if "sql" in tar_file[0]:
				tar_file.extract(tar_file[0], self.bkdir)
				sql_file = self.bkdir + '/' + tar_file[0]
				os.system("mysql " + options + " < " + sql_file)
			pass
		else:
			print 'Unkown bakfile type!'
		
		pass
	
	def recover_incr(self, bakfilelist):
		options = '-h' + self.conf['serip'][0] + ' -u' + self.conf['seruser'][0] \
				+ ' -p' + self.conf['serpass'][0]
		
		pass
	
class ConnOracle(object):
	
	def __init__(self, conf):
		self.conf = conf
		self.dbs = {}
		if utils.is_windows():
			self.bkdir = os.environ['TMP']
		elif utils.is_linux():
			self.bkdir = '/var/tmp/mysqlbak'
		else:
			print 'Unkown System Type!'
			sys.exit(1)
	
	def getdbs(self):
		try:
			dsn_tns = cx_Oracle.makedsn(self.conf['serip'][0], self.conf['serport'][0], 'hjctest1')
			print dsn_tns
			conn = cx_Oracle.connect(self.conf['seruser'][0], self.conf['serpass'][0], 
									dsn_tns)
			cursor = conn.cursor()
			cursor.execute('select tname from tab')
			rows = cursor.fetchall()
			keys = ('table',)
			self.dbs[keys] = rows
				
			cursor.close()
			conn.close()
			
			return sorted(self.dbs.iteritems(), key=lambda d:d[0])
		
		except cx_Oracle.Error, e:
			print 'Oracle Error %d: %s' % (e.args[0], e.args[1])
		raise
	
	def bk_now(self):
		pass
	
	def glob_bak(self):
		pass
	
	def incr_bak(self):
		pass
	
	def recover_glob(self, bakfile):
		pass
		
class ConnDatabase(object):
	
	def __init__(self, conf):
		self.conf = conf
		if self.conf['dbtype'][0] == "MySQL":
			self.conn = ConnMysql(self.conf)
		elif self.conf['dbtype'][0] == "Oracle":
			self.conn = ConnOracle(self.conf)
		else:
			print "Unkown Database Type!"
	
	def get(self):
		self.dbs = self.conn.getdbs()
		return self.dbs
	


if __name__ == '__main__':
	confOracle = {'serip':['172.31.201.241'], 'serport':['1522'],
		'seruser':['scott'], 'serpass':['admin']}
	confMysql = {'serip':['127.0.0.1'], 'serport':['3306'],
		'seruser':['root'], 'serpass':['root']}
	sys = utils.get_platform_name()
	# print sys, os.environ["TMP"]
	# con = ConnOracle(confOracle)
	# dbs = con.getdbs()
	# print dbs
	conn = ConnMysql(confMysql)
	print conn.logbinpath
	print os.path.basename(conn.logbinpath).split('.')
	print os.path.dirname(conn.logbinpath)
	print conn._get_logbin_last()
