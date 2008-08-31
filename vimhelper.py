import os

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


def findCompletions(cword, base, PYSMELLDICT):
    completions = []
    isAttrLookup = '.' in cword
    for module, moduleDict in PYSMELLDICT.items():
        if not isAttrLookup:
            completions.extend([{'word': word, 'kind': 'd', 'menu': module} for word in moduleDict['CONSTANTS']])
            completions.extend([getCompForFunction(func, module, 'f') for func in moduleDict['FUNCTIONS']])
        for klass, klassDict in moduleDict['CLASSES'].items():
            if not isAttrLookup:
                completions.append(dict(word=klass, kind='t', menu=module, abbr='%s(%s)' % (klass, _argsList(klassDict['constructor']))))
            else:
                completions.extend([dict(word=word, kind='m', menu='%s:%s' % (module, klass)) for word in klassDict['properties']])
                completions.extend([getCompForFunction(func, '%s:%s' % (module, klass), 'm') for func in klassDict['methods']])
    if base:
        filteredCompletions = [comp for comp in completions if comp['word'].startswith(base)]
    else:
        filteredCompletions = completions
    filteredCompletions.sort(sortCompletions)
    if len(filteredCompletions) == 1:
        #return the arg list instead
        oldComp = filteredCompletions[0]
        if oldComp['word'] == base:
            diff = len(oldComp['abbr']) - len(oldComp['word'])
            oldComp['word'] = oldComp['abbr']
    return filteredCompletions
    
def getCompForFunction(func, menu, kind):
    return dict(word=func[0], kind=kind, menu=menu,
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
    
    
