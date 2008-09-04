# vimhelper.py
# Companion to pysmell.vim
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# pysmell v0.2
# http://orestis.gr

# Released subject to the BSD License 

import os
import re

def findBase(vim):
    row, col = vim.current.window.cursor
    line = vim.current.buffer[row-1]
    index = col
    # col points at the end of the completed string
    # so col-1 is the last character of base
    while index > 0:
        index -= 1
        if line[index] in '. ':
            index += 1
            break
    return index #this is zero based :S
    
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

def matchCaseInsetively(base):
    return lambda comp: comp.lower().startswith(base.lower())

def matchCaseSensitively(base):
    return lambda comp: comp.startswith(base)

def camelGroups(word):
    groups = []
    rest = word
    while rest:
        i, limit = 0, len(rest)
        while i < limit:
            suspect = rest[1:i+1]
            if i and not (suspect.islower() and suspect.isalnum()):
                break
            i += 1
        part, rest = rest[:i], rest[i:]
        groups.append(part)
    return groups

def matchCamelCasedPrecise(base):
    baseGr = camelGroups(base)
    baseLen = len(baseGr)
    def check(comp):
        compGr = camelGroups(comp)
        return baseLen <= len(compGr) and all(matchCaseSensitively(bg)(cg) for bg, cg in zip(baseGr, compGr))
    return check

def matchCamelCased(base):
    baseGr = camelGroups(base)
    baseLen = len(baseGr)
    def check(comp):
        compGr = camelGroups(comp)
        return baseLen <= len(compGr) and all(matchCaseInsetively(bg)(cg) for bg, cg in zip(baseGr, compGr))
    return check

def matchSmartass(base):
    rev_base_letters = list(reversed(base.lower()))
    def check(comp):
        stack = rev_base_letters[:]
        for group in camelGroups(comp):
            lowered = group.lower()
            while True:
                if lowered and stack:
                    if lowered.startswith(stack[-1]):
                        stack.pop()
                    lowered = lowered[1:]
                else:
                    break
        return not stack
    return check

def matchFuzzyCS(base):
    regex = re.compile('.*'.join([] + list(base) + []))
    return lambda comp: bool(regex.match(comp))

def matchFuzzyCI(base):
    regex = re.compile('.*'.join([] + list(base) + []), re.IGNORECASE)
    return lambda comp: bool(regex.match(comp))

def findCompletions(vim, origLine, origCol, base, PYSMELLDICT):
    doesMatch = {
        'case-sensitive': matchCaseSensitively,
        'case-insensitive': matchCaseInsetively,
        'camel-case': matchCamelCased,
        'camel-case-sensitive': matchCamelCasedPrecise,
        'smartass': matchSmartass,
        'fuzzy-ci': matchFuzzyCI,
        'fuzzy-cs': matchFuzzyCS,
    }.get(vim.eval('g:pysmell_matcher'), matchCaseInsetively)(base)
    leftSide, rightSide = origLine[:origCol], origLine[origCol:]
    isAttrLookup = '.' in leftSide
    isArgCompletion = base.endswith('(') and leftSide.endswith(base)
    if isArgCompletion:
        lindex = 0
        if isAttrLookup:
            lindex = leftSide.rindex('.') + 1
        funcName = leftSide[lindex:-1].lstrip()

    completions = _createCompletionList(PYSMELLDICT, isAttrLookup)

    if base and not isArgCompletion:
        filteredCompletions = [comp for comp in completions if doesMatch(comp['word'])]
    elif isArgCompletion:
        filteredCompletions = [comp for comp in completions if comp['word'] == funcName]
    else:
        filteredCompletions = completions
    filteredCompletions.sort(sortCompletions)

    if filteredCompletions and isArgCompletion:
        #return the arg list instead
        oldComp = filteredCompletions[0]
        if oldComp['word'] == funcName:
            rindex = None
            if rightSide.startswith(')'):
                rindex = -1
            oldComp['word'] = oldComp['abbr'][:rindex]
    return filteredCompletions

def _createCompletionList(PYSMELLDICT, isAttrLookup):
    completions = []
    for module, moduleDict in PYSMELLDICT.items():
        if not isAttrLookup:
            completions.extend([dict(word=word, kind='d', menu=module, dup='1') for
                                    word in moduleDict['CONSTANTS']])
            completions.extend([getCompForFunction(func, module, 'f') for func
                                    in moduleDict['FUNCTIONS']])
        for klass, klassDict in moduleDict['CLASSES'].items():
            if not isAttrLookup:
                completions.append(dict(word=klass, kind='t', menu=module, dup='1',
                                abbr='%s(%s)' % (klass, _argsList(klassDict['constructor']))))
            else:
                completions.extend([dict(word=word, kind='m', dup='1', menu='%s:%s' %
                                (module, klass)) for word in klassDict['properties']])
                completions.extend([getCompForFunction(func, '%s:%s' % (module,
                            klass), 'm') for func in klassDict['methods']])
    
    return completions

def getCompForFunction(func, menu, kind):
    return dict(word=func[0], kind=kind, menu=menu, dup='1',
                            abbr='%s(%s)' % (func[0], _argsList(func[1])))
def _argsList(l):
     return ', '.join([str(arg) for arg in l])

def sortCompletions(comp1, comp2):
    word1, word2 = comp1['word'], comp2['word']
    return _sortCompletions(word1, word2)

def _sortCompletions(word1, word2):
    if word1.startswith('_'):
        return _sortCompletions(word1[1:], word2) + 2
    if word2.startswith('_'):
        return _sortCompletions(word1, word2[1:]) - 2
    return cmp(word1, word2)
    
def findPYSMELLDICT(filename):
    directory, basename = os.path.split(filename)
    partialDict = {}
    while not os.path.exists(os.path.join(directory, 'PYSMELLTAGS')):
        if os.path.exists(os.path.join(directory, 'PYSMELLTAGS.partial')):
            tagsFile = os.path.join(directory, 'PYSMELLTAGS.partial')
            partialDict.update(eval(file(tagsFile).read()))
        directory, _ = os.path.split(directory)
    tagsFile = os.path.join(directory, 'PYSMELLTAGS')
    if not os.path.exists(tagsFile):
        print 'Could not file PYSMELLTAGS for omnicompletion'
        return
    PYSMELLDICT = eval(file(tagsFile).read())
    PYSMELLDICT.update(partialDict)
    return PYSMELLDICT
