
# -*-coding:utf-8 -*-
'''
Created on 2013-2-18

@author: Administrator

本文件主要定义了文件解析类ConfigFilePraser，用于解析类似于以下格式的配置文件：
[key:value]
key1=value1
...

'''
import os
import ConfigParser

class ParseError(Exception):
    '''
                    错误解析函数，负责输出错误信息。
    '''
    def __init__(self, message, lineno, line):
        self.msg = message
        self.line = line
        self.lineno = lineno

    def __str__(self):
        return 'at line %d, %s: %r' % (self.lineno, self.msg, self.line)


class ConfigFilePraser(object):
    lineNo = 0
    parse_exc = ParseError
    
    def __init__(self, filepath): 
        self.config = ConfigParser.ConfigParser()
        self.file = filepath
        self.config.read(self.file)
        self.servers = []
        

    def __str__(self):
        for dictTmp in self.servers:
            for key in dictTmp.keys():
                print "%s: \t %s " % (key, dictTmp[key])
            
            print "\n"
    
    def _get_section(self, line):
        '''
                                负责解析含有'[]‘的行，相当于某一节的命名信息。
        '''
        if line[-1] != ']':
            return self.error_no_section_end_bracket(line)
        if len(line) <= 2:
            return self.error_no_section_name(line)
        
        return line[1:-1]
    
    def _split_key_value(self, line):
        '''
                                分离一行的信息，以键值对的形式返回。
        '''
        colon = line.find(':')
        equal = line.find('=')
        if colon < 0 and equal < 0:
            return self.error_invalid_assignment(line)
        
        if colon < 0 or (equal >= 0 and equal < colon):
            key, value = line[:equal], line[equal + 1:]
        else:
            key, value = line[:colon], line[colon + 1:]
            
        value = value.strip()
        if ((value and value[0] == value[-1]) and
            (value[0] == "\"" or value[0] == "'")):
            value = value[1:-1]
            
        return key.strip(), [value]
	
    def load(self, sectionlength):
        '''
                                装载某个配置文件，sectionlength指定了一节的行货，包括节头含有'[]'的那行。
        '''
        try:
            fp = open(self.file, "r")
        except IOError:
            raise IOError
        key = None
        value = []

        self.serDict = {}

        for line in fp:
            line = line.rstrip()
            
            if not line or line[0] in (' ', '\t'):
                continue
                
            if line[0] == '[':
                # Section start
                self.lineNo += 1
                section = self._get_section(line)               
                key, value = self._split_key_value(section)
                if key:
                    self.serDict[key] = value
            elif line[0] in '#;':
                self.comment(line[1:].lstrip())
            else:
                key, value = self._split_key_value(line)
                if not key:
                    return self.error_empty_key(line)
                else:
                    self.lineNo += 1
                    self.serDict[key] = value
            
            if self.serDict.__len__() % sectionlength == 0:
                self.servers.append(self.serDict.copy())
                self.serDict.clear()
        fp.close()
        return self.servers
                
    def save(self, serverInfo):
        '''
                                保存给定字典内键值对到配置文件中。
        '''
        
        sec = None
        
        if 'server' in serverInfo.keys():
            sec = 'server' + ":" + serverInfo['server']
            try:
                if sec not in self.config.sections():
                    self.config.add_section(sec)    
                for key in serverInfo.keys():
                    if key != 'server':
                        self.config.set(sec, key, serverInfo[key])
            except:
                raise self.parse_exc('Repeated section', self.lineNo)                
        else:
            raise self.parse_exc('Invalid section', self.lineNo)
        
        fp = open(self.file, "w+")
        self.config.write(fp)
        fp.close()
        
    def delete(self, sectionInfo):
        self.config.remove_section('server:' + sectionInfo['server'][0])
        print self.config.sections()
        fp = open(self.file, "w+")
        self.config.write(fp)
        fp.close()
            
    def assignment(self, key, value):
        """Called when a full assignment is parsed"""
        raise NotImplementedError()

    def new_section(self, section):
        """Called when a new section is started"""
        raise NotImplementedError()

    def comment(self, comment):
        """Called when a comment is parsed"""
        pass

    def error_invalid_assignment(self, line):
        raise self.parse_exc("No ':' or '=' found in assignment",
                             self.lineNo, line)

    def error_empty_key(self, line):
        raise self.parse_exc('Key cannot be empty', self.lineNo, line)

    def error_unexpected_continuation(self, line):
        raise self.parse_exc('Unexpected continuation line',
                             self.lineNo, line)

    def error_no_section_end_bracket(self, line):
        raise self.parse_exc('Invalid section (must end with ])',
                             self.lineNo, line)

    def error_no_section_name(self, line):
        raise self.parse_exc('Empty section name', self.lineNo, line)
        

	
if __name__ == '__main__':
    filepath = os.path.dirname(os.getcwd()) + "\\conf\\Server.conf"
    config = ConfigFilePraser(filepath)
    servers = config.load(13)
    print config.config.sections()
    for dict in servers:
        if dict['server'][0] == 'oracletest':
            config.delete(dict)


