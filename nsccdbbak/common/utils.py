'''
Created on 2013-4-18

@author: Administrator
'''
import os
import sys

PLATFORM_WINDOWS = 'windows'
PLATFORM_LINUX = 'linux'
PLATFORM_BSD = 'bsd'
PLATFORM_DARWIN = 'darwin'
PLATFORM_UNKNOWN = 'unknown'

def get_platform_name():
	if sys.platform.startswith("win"):
		return PLATFORM_WINDOWS
	elif sys.platform.startswith("linux"):
		return PLATFORM_LINUX
	elif sys.platform.startswith("bsd"):
		return PLATFORM_BSD
	elif sys.platform.startswith("darwin"):
		return PLATFORM_DARWIN

__platform__ = get_platform_name()

def is_windows():
	return __platform__ == PLATFORM_WINDOWS

def is_linux():
	return __platform__ == PLATFORM_LINUX

def is_bsd():
	return __platform__ == PLATFORM_BSD

def is_darwin():
	return __platform__ == PLATFORM_DARWIN
	
def hostname():  
	if is_windows():  
		hostname = os.getenv('computername')  
		return hostname  

	elif is_linux:  
		host = os.popen('echo $HOSTNAME')  
		try:  
			hostname = host.read()  
			return hostname  
		finally:  
			host.close()  
	else:  
		return 'Unkwon hostname'  

if __name__ == '__main__':
	print hostname()