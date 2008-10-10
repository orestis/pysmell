# idehelper.py
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 

import os
from codefinder import infer, findRootPackageList
from matchers import MATCHERS
from dircache import listdir
import fnmatch

def updatePySmellDict(master, partial):
    for key, value in partial.items():
        if isinstance(value, dict):
            master.setdefault(key, {}).update(value)
        elif isinstance(value, list):
            master.setdefault(key, []).extend(value)


def tryReadPYSMELLDICT(directory, filename, dictToUpdate):
    if os.path.exists(os.path.join(directory, filename)):
        tagsFile = file(os.path.join(directory, filename))
        try:
            updatePySmellDict(dictToUpdate, eval(tagsFile.read()))
        finally:
            tagsFile.close()
    

def findPYSMELLDICT(filename):
    directory, basename = os.path.split(filename)
    PYSMELLDICT = {}
    while not os.path.exists(os.path.join(directory, 'PYSMELLTAGS')) and basename:
        for tagsfile in fnmatch.filter(listdir(directory), 'PYSMELLTAGS.*'):
            tryReadPYSMELLDICT(directory, tagsfile, PYSMELLDICT)
        directory, basename = os.path.split(directory)

    for tagsfile in fnmatch.filter(listdir(directory), 'PYSMELLTAGS.*'):
        tryReadPYSMELLDICT(directory, tagsfile, PYSMELLDICT)
    tagsPath = os.path.join(directory, 'PYSMELLTAGS')
    if not os.path.exists(tagsPath):
        print 'Could not file PYSMELLTAGS for omnicompletion'
        return
    tryReadPYSMELLDICT(directory, 'PYSMELLTAGS', PYSMELLDICT)
    return PYSMELLDICT


def debug(vim, msg):
    if vim is None: return
    if int(vim.eval('g:pysmell_debug')):
        debBuffer = None
        for b in vim.buffers:
            if b.name.endswith('DEBUG'):
                debBuffer = b
        debBuffer.append(msg)


def inferClass(fullPath, origSource, origLineNo, PYSMELLDICT, vim=None):
    pathParts = []
    fullPath = fullPath
    head, tail = os.path.split(fullPath[:-3])
    pathParts.append(tail)
    while head and tail:
        head, tail = os.path.split(head)
        if tail:
            pathParts.append(tail)
    pathParts.reverse()
    klass, parents = infer(origSource, origLineNo)
    # replace POINTERS with their full reference
    for index, parent in enumerate(parents):
        if parent in PYSMELLDICT['POINTERS']:
            parents[index] = PYSMELLDICT['POINTERS'][parent]
        else:
            for pointer in PYSMELLDICT['POINTERS']:
                if pointer.endswith('*') and parent.startswith(pointer[:-2]):
                    parents[index] = '%s.%s' % (PYSMELLDICT['POINTERS'][pointer][:-2], parent.split('.', 1)[-1])


    fullKlass = klass
    while pathParts:
        fullKlass = "%s.%s" % (pathParts.pop(), fullKlass)
        if fullKlass in PYSMELLDICT['CLASSES'].keys():
            break
    else:
        # we don't know about this class, look in the file system
        path, filename = os.path.split(fullPath)
        packages = findRootPackageList(path, filename)
        fullKlass = "%s.%s.%s" % (".".join(packages), filename[:-3], klass)
        
    return fullKlass, parents


class CompletionOptions(object):
    def __init__(self, **kwargs):
        self._dict = dict(isAttrLookup=False, klass=None, parents=[],
                        funcName=None, rindex=None, module=None, completeModule=False)
        self._dict.update(kwargs)

    def __getattr__(self, item):
        return self._dict[item]
        
    def __eq__(self, other):
        return self._dict == other._dict

    def __repr__(self):
        return repr(self._dict)
        

def detectCompletionType(fullPath, origSource, origLineText, origLineNo, origCol, base, PYSMELLDICT):
    leftSide, rightSide = origLineText[:origCol], origLineText[origCol:]

    klass = None
    rindex = None
    funcName = None
    parents = None
    module = None
    completeModule = False

    isModCompletion = (leftSide.lstrip().startswith("from") or leftSide.lstrip().startswith("import"))
    if isModCompletion:
        module = leftSide.split(" ")[1]
        if "." in module and " import " not in leftSide:
            module, _ = module.rsplit(".", 1)
        if "import " in leftSide:
            completeModule = True


    
    isAttrLookup = "." in leftSide and not isModCompletion
    isClassLookup = isAttrLookup and leftSide[:leftSide.rindex('.')].endswith('self')
    if isClassLookup:
        klass, parents = inferClass(fullPath, origSource, origLineNo, PYSMELLDICT)

    isArgCompletion = base.endswith('(') and leftSide.endswith(base)
    if isArgCompletion:
        lindex = 0
        if isAttrLookup:
            lindex = leftSide.rindex('.') + 1
        funcName = leftSide[lindex:-1].lstrip()
        if rightSide.startswith(')'):
            rindex = -1

    return CompletionOptions(isAttrLookup=isAttrLookup, klass=klass,
                            parents=parents, funcName=funcName, rindex=rindex, module=module, completeModule=completeModule)


def findCompletions(base, PYSMELLDICT, options, matcher=None):
    doesMatch = MATCHERS[matcher](base)

    funcName = options.funcName

    if options.module is not None:
        completions = _createModuleCompletions(PYSMELLDICT, options.module, options.completeModule)
    else:
        completions = _createCompletionList(PYSMELLDICT, options.isAttrLookup, options.klass, options.parents)

    if base and not funcName:
        filteredCompletions = [comp for comp in completions if doesMatch(comp['word'])]
    elif funcName:
        filteredCompletions = [comp for comp in completions if comp['word'] == funcName]
    else:
        filteredCompletions = completions

    filteredCompletions.sort(sortCompletions)

    if filteredCompletions and funcName:
        #return the arg list instead
        oldComp = filteredCompletions[0]
        if oldComp['word'] == funcName:
            oldComp['word'] = oldComp['abbr'][:options.rindex]
    return filteredCompletions


def _createModuleCompletions(PYSMELLDICT, module, completeModule):
    completions = []
    splitModules = set()
    for reference in PYSMELLDICT['HIERARCHY']:
        if not reference.startswith(module): continue
        if reference == module: continue
        rest = reference[len(module)+1:]
        if '.' in rest:
            rest = rest.split(".", 1)[0]
        if rest:
            splitModules.add(rest)
    if completeModule:
        members = _createCompletionList(PYSMELLDICT, False, False, False)
        completions.extend(comp for comp in members if comp["menu"] == module)
        pointers = []
        for p in PYSMELLDICT['POINTERS']:
            if p.startswith(module) and '.' not in p[len(module)+1:]:
                basename = p[len(module)+1:]
                if p.endswith("*"):
                    v = PYSMELLDICT['POINTERS'][p][:-2] # remove .*
                    completions.extend(_createModuleCompletions(PYSMELLDICT, v, True))
                else:
                    splitModules.add(basename)
                
                
    completions.extend(dict(word=name, kind="t", dup="1") for name in splitModules)
    return completions


def _createCompletionList(PYSMELLDICT, isAttrLookup, klass, parents):
    completions = []
    if not isAttrLookup:
        completions.extend([_getCompForConstant(word) for word in PYSMELLDICT['CONSTANTS']])
        completions.extend([_getCompForFunction(func, 'f') for func in PYSMELLDICT['FUNCTIONS']])
        completions.extend([_getCompForConstructor(klass, klassDict) for (klass, klassDict) in PYSMELLDICT['CLASSES'].items()])
    elif klass:
        completions.extend(getCompletionsForClass(klass, parents, PYSMELLDICT))
    else: #plain attribute lookup
        for klass, klassDict in PYSMELLDICT['CLASSES'].items():
            addCompletionsForClass(klass, klassDict, completions)
    
    return completions

def getCompletionsForClass(klass, parents, PYSMELLDICT):
        klassDict = PYSMELLDICT['CLASSES'].get(klass, None)
        completions = []
        ancestorList = []
        nonBuiltinParents = [p for p in parents if p not in __builtins__]
        if klassDict is None and not nonBuiltinParents:
            return completions
        elif klassDict is None and nonBuiltinParents:
            for anc in nonBuiltinParents:
                _findAllParents(anc, PYSMELLDICT['CLASSES'], ancestorList)
                ancDict = PYSMELLDICT['CLASSES'].get(anc, None)
                if ancDict is None: continue
                addCompletionsForClass(anc, ancDict, completions)
            for anc in ancestorList:
                ancDict = PYSMELLDICT['CLASSES'].get(anc, None)
                if ancDict is None: continue
                addCompletionsForClass(anc, ancDict, completions)
            return completions
            
        _findAllParents(klass, PYSMELLDICT['CLASSES'], ancestorList)
        addCompletionsForClass(klass, klassDict, completions)
        for anc in ancestorList:
            ancDict = PYSMELLDICT['CLASSES'].get(anc, None)
            if ancDict is None: continue
            addCompletionsForClass(anc, ancDict, completions)
        return completions


def addCompletionsForClass(klass, klassDict, completions):
    module, klassName = klass.rsplit('.', 1)
    completions.extend([dict(word=prop, kind='m', dup='1', menu='%s:%s' %
                    (module, klassName)) for prop in klassDict['properties']])
    completions.extend([_getCompForFunction(func, 'm', module='%s:%s' % (module,
                klassName)) for func in klassDict['methods']])


def _findAllParents(klass, classesDICT, ancList):
    klassDict = classesDICT.get(klass, None)
    if klassDict is None: return
    for anc in klassDict['bases']:
        if anc in __builtins__: continue
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
