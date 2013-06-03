import os, sys
tmp = os.path


print os.path.abspath(sys.executable)

path =  sys.path

for i in xrange(len(path)):
    if "nsccdbbak" in path[i]:
        print path[i]
        