
import unittest
from subprocess import Popen, PIPE

from nsccdbbak.common.connDatabase import ConnDatabase
from nsccdbbak.common.connStorage import ConnStorage

class AllModuleTestCase(unittest.TestCase):
	# 
	def testConnDatabaseWithPyChecker(self):
		cmd = 'pychecker', '-Q', ConnDatabase.__file__
		pychecker = Popen(cmd, stdout=PIPE, stderr=PIPE)
		self.assertEqual(pychecker.stdout.read(), '')

	def testConnDatabaseWithPyLint(self):
		cmd = 'pyLint', '-rn', 'ConnDatabase'
		pylint = Popen(cmd, stdout=PIPE, stderr=pip===PIPE)
		self.asserEqual(pylint.stdout.read(), '')


if __name__ = '__main__':
	unittest.main()
