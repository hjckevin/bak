# -*-coding:utf-8 -*-
'''
Created on 2013-2-18

@author: Administrator
'''

import os
import sys
import re
import time
import zipfile
import tarfile
import ConfigParser

from os.path import join as pathjoin

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
		if not os.path.exists(self.bkdir):
			os.mkdir(self.bkdir)
		self.conf = conf
		self.dbs = {}
		self.conn = MySQLdb.connect(host=self.conf['serip'], 
									user=self.conf['seruser'], 
									passwd=self.conf['serpass'])
		self.logbinpath = self._get_logbin_path()
		
	def _get_logbin_path(self):
		'''
		获取MySQL二进制日志文件的路径，要求在mysql的配置文件中设定log-bin选项。这里有三种情况：
		1. log-bin= ：即为空，此时MySQL自动将日志文件存放到$datadir中，并以$hostname-bin.index/0000001的格式命令。
		2. log-bin=filename.* : 指定文件名，此时日志文件同样存放到$datadir中，但是以filename.index/0000001的格式命令。
		3. log-bin=filepath/filename.* : 此时日志文件存放到filepath路径下，以filename.index/0000001的格式命令。
		'''
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
		
		if logbin_path is None or os.path.dirname(logbin_path) is None:
			cursor = self.conn.cursor()
			cursor.execute("show variables like 'datadir'")
			datadir = cursor.fetchall()[0][1]
			cursor.close()
			if logbin_path is None:
				return pathjoin(datadir.strip('\"'), utils.hostname() + '-bin')
			else:
				return pathjoin(datadir.strip('\"'), logbin_path.split('.')[0])
		elif os.path.dirname(logbin_path) is not None:
			cursor.close()
			return logbin_path.strip('\"')
		else:
			print "log-bin unset!"
		
	def _get_logbin_last(self):
		logbin_index = pathjoin(os.path.dirname(self.logbinpath), \
					os.path.basename(self.logbinpath).split('.')[0] + '.index')
		fp = open(logbin_index)
		logbin_filelist = fp.readlines()
		
		return pathjoin(os.path.dirname(self.logbinpath), \
               os.path.basename(logbin_filelist[len(logbin_filelist) - 2]).strip('\n'))
		
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
		timestamp = str(time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time())))
		
		if utils.is_windows():
			dump_dir = self.bkdir + '\\' + timestamp
			dump_file = dump_dir + '\\' + timestamp + '_glob.sql'
			zip_file_path = dump_dir + '\\' + timestamp + '_glob.zip'
			log_file = dump_dir + '\\' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' --all-databases '
			
			os.mkdir(dump_dir)
			os.system('purge master logs')
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				myzipfile = zipfile.ZipFile(zip_file_path, 'w')
				myzipfile.write(dump_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed!" >> ' + log_file)
				return False, None
		elif utils.is_linux():
			dump_dir = self.bkdir + '/' + timestamp
			dump_file = dump_dir + '/' + timestamp + '_glob.sql'
			tar_file = dump_dir + '/' + timestamp + '_glob.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' --all-databases '
			
			os.mkdir(dump_dir)
			os.system('purge master logs')
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(dump_file)
				tarfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, tar_file
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		else:
			print 'Unkown System Type!'
			sys.exit(1)
	
	def glob_bak(self):
		timestamp = str(time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time())))
		
		if utils.is_windows():
			dump_dir = self.bkdir + '\\' + timestamp
			dump_file = dump_dir + '\\' + timestamp + '_glob.sql'
			zip_file_path = dump_dir + '\\' + timestamp + '_glob.zip'
			log_file = dump_dir + '\\' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' --all-databases --flush-logs --master-data=2'
			
			os.mkdir(dump_dir)
			os.system('purge master logs')
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				myzipfile = zipfile.ZipFile(zip_file_path, 'w')
				myzipfile.write(dump_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		elif utils.is_linux():
			dump_dir = self.bkdir + '/' + timestamp
			dump_file = dump_dir + '/' + timestamp + '_glob.sql'
			tar_file = dump_dir + '/' + timestamp + '_glob.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_glob.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' --all-databases --flush-logs --master-data=2'
			
			os.mkdir(dump_dir)
			os.system('purge master logs')
			if os.system('mysqldump ' + options + ' > ' + dump_file) == 0:
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(dump_file)
				tarfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, tar_file
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		else:
			print 'Unkown System Type!'
			sys.exit(1)
	
	def incr_bak(self):
		timestamp = str(time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time())))
		
		if utils.is_windows():
			dump_dir = self.bkdir + '\\' + timestamp
			zip_file_path = dump_dir + '\\' + timestamp + '_incr.zip'
			log_file = dump_dir + '\\' + timestamp + '_incr.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' flush-logs'
			
			os.mkdir(dump_dir)
			if os.system('mysqladmin ' + options) == 0:
				logbin_file = self._get_logbin_last()
				print logbin_file
				myzipfile = zipfile.ZipFile(zip_file_path, 'w')
				myzipfile.write(logbin_file)
				myzipfile.close()
				os.system('echo "DataBase Backup Success!" >> ' + log_file)
				return True, zip_file_path
			else:
				os.system('echo "DataBase Backup Failed! >> ' + log_file)
				return False, None
		elif utils.is_linux():
			dump_dir = self.bkdir + '/' + timestamp
			tar_file = dump_dir + '/' + timestamp + '_incr.tar.gz'
			log_file = dump_dir + '/' + timestamp + '_incr.log'
			options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
					+ ' -p' + self.conf['serpass'] + ' flush-logs'
			
			os.mkdir(dump_dir)
			if os.system('mysqladmin ' + options) == 0:
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
		options = '-h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
				+ ' -p' + self.conf['serpass']
		
		if zipfile.is_zipfile(bakfile):
			file_obj = zipfile.ZipFile(bakfile)
			file_name = file_obj.namelist()[0]
			sql_file = open(pathjoin(self.bakdir, os.path.basename(file_name)), 'wb')
			sql_file.write(file_obj.read(file_name))
			sql_file.close()
			os.system('mysql ' + options + " < " + sql_file.name)
		elif tarfile.is_tarfile(bakfile):
			tar_file = tarfile.open(bakfile, 'r|gz')
			if "sql" in tar_file[0]:
				tar_file.extract(tar_file[0], self.bkdir)
				sql_file = self.bkdir + '/' + tar_file[0]
				os.system('mysql ' + options + " < " + sql_file)
			pass
		else:
			print 'Unkown bakfile type!'
	
	def recover_incr(self, bakfilelist):
		options = ' -h' + self.conf['serip'] + ' -u' + self.conf['seruser'] \
				+ ' -p' + self.conf['serpass']
		if zipfile.is_zipfile(bakfilelist[0]):
			for bakfile in bakfilelist:
				file_obj = zipfile.ZipFile(bakfile)
				file_name = file_obj.namelist()[0]
				sql_file = open(pathjoin(self.bakdir, os.path.basename(file_name)), 'wb')
				sql_file.write(file_obj.read(file_name))
				sql_file.close()
				os.system('mybinlog ' + sql_file.name + ' | mysql ' + options)           
		elif tarfile.is_tarfile(bakfilelist[0]):
			for bakfile in bakfilelist:
				tar_file = tarfile.open(bakfile, 'r|gz')
				tar_file.extract(tar_file[0], self.bkdir)
				sql_file = self.bkdir + '/' + tar_file[0]
				os.system('mybinlog ' + sql_file.name + ' | mysql ' + options)
					
		else:
			print 'Unkown bakfile type!'
		pass
	
class ConnOracle(object):
	
	def __init__(self, conf):
		self.conf = conf
		self.dbs = {}
		if utils.is_windows():
			self.bkdir = os.environ['TMP']
		elif utils.is_linux():
			self.bkdir = '/var/tmp/oraclebak'
		else:
			print 'Unkown System Type!'
			sys.exit(1)
		if not os.path.exists(self.bkdir):
			os.mkdir(self.bkdir)
	
	def getdbs(self):
		'''
		获取用户空间内的表信息
		'''
		try:
			dsn_tns = cx_Oracle.makedsn(self.conf['serip'], self.conf['serport'], 'testorcl')
			print dsn_tns
			conn = cx_Oracle.connect(self.conf['seruser'], self.conf['serpass'], 
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
	
	def bk_now(self, tables=None):
		'''
		使用逻辑备份导出指定用户的数据表，参数tables为表名元组，默认为空时导出整个用户空间。
		'''
		timestamp = str(time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time())))
		
		if utils.is_windows():
			bak_dir = self.bkdir + '\\' + timestamp
			dmp_file = bak_dir + '\\' + timestamp + '_exp.dmp'
			log_file = bak_dir + '\\' + timestamp + '_exp.log'
			options = self.conf['seruser'] + '/' + self.conf['serpass'] + ' buffer=64000 file=' \
				+ dmp_file + ' log=' + log_file
			if tables is not None:
				options += ' tables=' + tables
			else:
				options += ' owner=' + self.conf['seruser']
			os.mkdir(bak_dir)
			if os.system('exp ' + options) == 0:
				zip_file = bak_dir + '\\' + timestamp + '_exp.zip'
				myzipfile = zipfile.ZipFile(zip_file, 'w')
				myzipfile.write(dmp_file)
				myzipfile.close()
				return True, zip_file
			else:
				print 'backup oprations failed!'
				return False, None
		elif utils.is_linux():
			bak_dir = self.bkdir + '/' + timestamp
			dmp_file = bak_dir + '/' + timestamp + '_exp.dmp'
			log_file = bak_dir + '/' + timestamp + '_exp.log'
			options = self.conf['seruser'] + '/' + self.conf['serpass'] + ' buffer=64000 file=' \
				+ dmp_file + ' log=' + log_file
			if tables is not None:
				options += ' tables=' + tables
			else:
				options += ' owner=' + self.conf['seruser']
			os.mkdir(bak_dir)
			if os.system('exp ' + options) == 0:
				tar_file = bak_dir + '/' + timestamp + '_exp.tar.gz'
				tarfile = tarfile.open(tar_file, 'w:gz')
				tarfile.add(dmp_file)
				tarfile.close()
				return True, tar_file
		else:
			print 'Unkown System Type!'
			sys.exit(1)
		

	def glob_bak(self):
		pass
	
	def incr_bak(self):
		pass
	
	def recover_glob(self, bakfile):
		options = self.conf['seruser'] + '/' + self.conf['serpass'] + ' fromuser=' + self.conf['seruser'] \
				+ ' touser=' + self.conf['seruser'] + 'buffer=64000 file='
		if 'exp' in bakfile:
			if zipfile.is_zipfile(bakfile):
				file_obj = zipfile.ZipFile(bakfile)
				file_name = file_obj.namelist()[0]
				dmp_file = open(self.bakdir + '\\' + file_name, 'wb')
				dmp_file.write(file_obj.read(file_name))
				dmp_file.close()
				log_file = self.bkdir + '\\' + file_name.split('.')[0] + '.log'
				if os.system('imp ' + options + dmp_file + ' log=' + log_file) == 0:
					return True, log_file
				else:
					return False, log_file
			elif tarfile.is_tarfile(bakfile):
				tar_file = tarfile.open(bakfile, 'r|gz')
				log_file = self.bkdir + '/' + file_name.split('.')[0] + '.log'
				tar_file.extract(tar_file[0], self.bkdir)
				dmp_file = self.bkdir + '/' + tar_file[0]
				if os.system('imp ' + options + dmp_file + ' log=' + log_file) == 0:
					return True, log_file
				else:
					return False, log_file
			else:
				return False, 'Unkown bakfile type!'
		else:
			return False, 'Unkown bakfile type!'
		pass
		
class ConnDatabase(object):
	
	def __init__(self, conf):
		self.conf = conf
		print conf
		if self.conf['dbtype'] == "MySQL":
			self.conn = ConnMysql(self.conf)
		elif self.conf['dbtype'] == "Oracle":
			self.conn = ConnOracle(self.conf)
		else:
			print "Unkown Database Type!"
	
	def get(self):
		self.dbs = self.conn.get_dbs()
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
	print os.path.basename(conn.logbinpath).split('.')[0]
	print os.path.dirname(conn.logbinpath)
	print conn._get_logbin_last()
	
#	logbin_file = conn._get_logbin_last()
#	timestamp = str(time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time())))
#	dump_dir = pathjoin(conn.bkdir, timestamp)
#	dump_file = pathjoin(dump_dir, timestamp + '_glob.sql')
#	tar_file = pathjoin(dump_dir, timestamp + '_incr.tar.gz')
#	print tar_file
#	tarfile = tarfile.open(tar_file, 'w:gz')
#	tarfile.add(logbin_file)
#	tarfile.close()
#	import doctest
#	doctest.testmod(ConnDatabase)
	
	