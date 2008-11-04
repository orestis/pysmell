# vimhelper.py
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 
def findWord(vim, origCol, origLine):
    # vim moves the cursor and deletes the text by the time we are called
    # so we need the original position and the original line...
    index = origCol
    while index > 0:
        index -= 1
        if origLine[index] == ' ':
            index +=1
            break
    cword = origLine[index:origCol]
    return cword

    
