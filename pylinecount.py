#!/usr/bin/python2

'''
Line Counter Script

Counts the amount of lines within python files 
that exist in current working directory, or otherwise
the specified directory. Includes sub directories in check.
'''

import sys, os

def fileLen(fname):
    i = 0
    try:
        with open(fname) as f:
            for i, l in enumerate(f):
                pass
    except IOError:
        print "file not found.: " + fname
    return i + 1
    
def chkFolder(folder):
    length = 0
    for (path, dirs, files) in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                p = os.path.join(path, file)
                fl = fileLen(p)
                length += fl
                print p + ": " + str(fl)
        for dir in dirs:
            length += chkFolder(os.path.join(folder, dir))
    return length

if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder = folder = sys.argv[1]
    else:
        folder = os.getcwd()
        
    isdir = os.path.isdir(folder)
    if isdir == True:
        length = chkFolder(folder) 
        print "-------------------"
        print "Package Line Count: " + str(length)
    else:
        print "Not A Directory."
            
