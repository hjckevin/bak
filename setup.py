import os
import sys
import setuptools

#from nsccdbbak.common import setup.py
#
#requires = parse_requirements()
#depend_links = parse_dependency_links()

setuptools.setup(
    name="nsccdbbak",
    version="2013.5",
    description="A backup system for mysql database, stores the backup file on Swift",
    author="nscc-tj",
    author_email="hanjc@nscc-tj.gov.cn",
    packages=['nsccdbbak', 'nsccdbbak/glade'],#setuptools.find_packages(exclude=['tests', 'tests.*']),
    scripts=[
		  'nsccdbbak/mainFrame.py',
	],
)
