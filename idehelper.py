import os
import re
from codefinder import infer

try:
    all
except:
     def all(iterable):
         for element in iterable:
             if not element:
                 return False
         return True
    
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

def debug(vim, msg):
    if vim is None: return
    if int(vim.eval('g:pysmell_debug')):
        debBuffer = None
        for b in vim.buffers:
            if b.name.endswith('DEBUG'):
                debBuffer = b
    debBuffer.append(msg)

def findCompletions(matcher, fullPath, origSource, origLineText, origLineNo, origCol, base, PYSMELLDICT, vim=None):
    doesMatch = {
        'case-sensitive': matchCaseSensitively,
        'case-insensitive': matchCaseInsetively,
        'camel-case': matchCamelCased,
        'camel-case-sensitive': matchCamelCasedPrecise,
        'smartass': matchSmartass,
        'fuzzy-ci': matchFuzzyCI,
        'fuzzy-cs': matchFuzzyCS,
    }.get(matcher, matchCaseInsetively)(base)
    leftSide, rightSide = origLineText[:origCol], origLineText[origCol:]
    isAttrLookup = '.' in leftSide
    isClassLookup = isAttrLookup and leftSide[:leftSide.rindex('.')].endswith('self')
    debug(vim, 'isClassLookup: %s' % isClassLookup)
    isArgCompletion = base.endswith('(') and leftSide.endswith(base)
    if isClassLookup:
        pathParts = []
        head, tail = os.path.split(fullPath[:-3])
        pathParts.append(tail)
        while head and tail:
            head, tail = os.path.split(head)
            if tail:
                pathParts.append(tail)
        pathParts.reverse()
        debug(vim, 'pathparts: %r' % pathParts)
        klass = infer(origSource, origLineNo)
        debug(vim, 'klass 1: %s' % klass)

        while klass not in PYSMELLDICT['CLASSES'].keys() and pathParts:
            klass = "%s.%s" % (pathParts.pop(), klass)
            
        debug(vim, 'klass 2: %s' % klass)

    if isArgCompletion:
        lindex = 0
        if isAttrLookup:
            lindex = leftSide.rindex('.') + 1
        funcName = leftSide[lindex:-1].lstrip()

    completions = _createCompletionList(PYSMELLDICT, isAttrLookup, isClassLookup and klass)

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

def _findAllParents(klass, classesDICT, ancList):
    klassDict = classesDICT.get(klass, None)
    if klassDict is None: return
    for anc in klassDict['bases']:
        if anc == 'object': continue
        ancList.append(anc)
        _findAllParents(anc, classesDICT, ancList)

def _getCompForConstant(word):
    module, const = word.rsplit('.', 1)
    return dict(word=const, kind='d', menu=module, dup='1')

def _getCompForFunction(func, kind, module=None):
    if module is None:
        module, funcName = func[0].rsplit('.', 1)
    else:
        funcName = func[0]
    return dict(word=funcName, kind=kind, menu=module, dup='1',
                            abbr='%s(%s)' % (funcName, _argsList(func[1])))

def _getCompForConstructor(klass, klassDict):
    module, klassName = klass.rsplit('.', 1)
    return dict(word=klassName, kind='t', menu=module, dup='1', abbr='%s(%s)' % (klassName, _argsList(klassDict['constructor'])))

def _createCompletionList(PYSMELLDICT, isAttrLookup, klass):
    completions = []
    if not isAttrLookup:
        completions.extend([_getCompForConstant(word) for word in PYSMELLDICT['CONSTANTS']])
        completions.extend([_getCompForFunction(func, 'f') for func in PYSMELLDICT['FUNCTIONS']])
        completions.extend([_getCompForConstructor(klass, klassDict) for (klass, klassDict) in PYSMELLDICT['CLASSES'].items()])
    elif klass:
        klassDict = PYSMELLDICT['CLASSES'].get(klass, None)
        if klassDict is None: return completions
        ancestorList = []
        _findAllParents(klass, PYSMELLDICT['CLASSES'], ancestorList)
        addCompletionsForClass(klass, klassDict, completions)
        for anc in ancestorList:
            ancDict = PYSMELLDICT['CLASSES'].get(anc, None)
            if ancDict is None: continue
            addCompletionsForClass(anc, ancDict, completions)

    else: #plain attribute lookup
        for klass, klassDict in PYSMELLDICT['CLASSES'].items():
            addCompletionsForClass(klass, klassDict, completions)
    
    return completions

def addCompletionsForClass(klass, klassDict, completions):
    module, klassName = klass.rsplit('.', 1)
    completions.extend([dict(word=prop, kind='m', dup='1', menu='%s:%s' %
                    (module, klassName)) for prop in klassDict['properties']])
    completions.extend([_getCompForFunction(func, 'm', module='%s:%s' % (module,
                klassName)) for func in klassDict['methods']])

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
