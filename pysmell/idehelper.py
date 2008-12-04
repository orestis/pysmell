# idehelper.py
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 

import __builtin__
import os, re
import fnmatch
from dircache import listdir

from pysmell.codefinder import findRootPackageList, getImports, getNames, getClassAndParents, analyzeFile, getSafeTree
from pysmell.matchers import MATCHERS

def findBase(line, col):
    index = col
    # col points at the end of the completed string
    # so col-1 is the last character of base
    while index > 0:
        index -= 1
        if line[index] in '. ':
            index += 1
            break
    return index #this is zero based :S
    

def updatePySmellDict(master, partial):
    for key, value in partial.items():
        if isinstance(value, dict):
            master.setdefault(key, {}).update(value)
        elif isinstance(value, list):
            master.setdefault(key, []).extend(value)


def tryReadPYSMELLDICT(directory, filename, dictToUpdate):
    if os.path.exists(os.path.join(directory, filename)):
        tagsFile = open(os.path.join(directory, filename), 'r')
        try:
            updatePySmellDict(dictToUpdate, eval(tagsFile.read()))
        finally:
            tagsFile.close()
    

def findPYSMELLDICT(filename):
    pathParts = _getPathParts(filename)[:-1]
    PYSMELLDICT = {}
    while pathParts:
        directory = os.path.join(*pathParts)
        for tagsfile in fnmatch.filter(listdir(directory), 'PYSMELLTAGS.*'):
            tryReadPYSMELLDICT(directory, tagsfile, PYSMELLDICT)
        tagsPath = os.path.join(directory, 'PYSMELLTAGS')
        if os.path.exists(tagsPath):
            tryReadPYSMELLDICT(directory, 'PYSMELLTAGS', PYSMELLDICT)
            break
        pathParts.pop()
    else:
        return None
    return PYSMELLDICT
            

def _getPathParts(path):
    "given a full path, return its components without the extension"
    head, tail = os.path.split(path[:-3])
    pathParts = [tail]
    while head and tail:
        head, tail = os.path.split(head)
        if tail:
            pathParts.append(tail)
    if head:
        pathParts.append(head)
    pathParts.reverse()
    return pathParts


def debug(vim, msg):
    if vim is None: return
    if int(vim.eval('g:pysmell_debug')):
        debBuffer = None
        for b in vim.buffers:
            if b.name.endswith('DEBUG'):
                debBuffer = b
        debBuffer.append(msg)


def inferModule(chain, AST, lineNo):
    imports = getImports(AST)
    fullModuleParts = []
    valid = False
    for part in chain.split('.'):
        if part in imports:
            fullModuleParts.append(imports[part])
            valid = True
        else:
            fullModuleParts.append(part)
    if valid:
        return '.'.join(fullModuleParts)
    return None
    

funcCellRE = re.compile(r'(.+)\(.*\)')
def inferInstance(fullPath, AST, lineNo, var, PYSMELLDICT):
    names, klasses = getNames(AST)
    assignment = names.get(var, None)
    klass = None
    parents = []
    if assignment:
        possibleMatch = funcCellRE.match(assignment)
        if possibleMatch:
            klass = possibleMatch.groups(1)[0]
            if klass in klasses:
                path, filename = os.path.split(fullPath)
                packages = findRootPackageList(path, filename)
                if packages:
                    packagesStr = (".".join(packages)) + "."
                else:
                    packagesStr = ""
                klass = "%s%s.%s" % (packagesStr, filename[:-3], klass)
            else:
                klass = _qualify(names.get(klass, klass), PYSMELLDICT)
            parents = PYSMELLDICT['CLASSES'].get(klass, {'bases': []})['bases']

    return klass, parents


def _qualify(thing, PYSMELLDICT):
    if thing in PYSMELLDICT['POINTERS']:
        return PYSMELLDICT['POINTERS'][thing]
    else:
        for pointer in PYSMELLDICT['POINTERS']:
            if pointer.endswith('*') and thing.startswith(pointer[:-2]):
                return '%s.%s' % (PYSMELLDICT['POINTERS'][pointer][:-2], thing.split('.', 1)[-1])
    return thing

def inferClass(fullPath, AST, origLineNo, PYSMELLDICT, vim=None):
    klass, parents = getClassAndParents(AST, origLineNo)

    # replace POINTERS with their full reference
    for index, parent in enumerate(parents[:]):
        parents[index] = _qualify(parent, PYSMELLDICT)

    pathParts = _getPathParts(fullPath)
    fullKlass = klass
    while pathParts:
        fullKlass = "%s.%s" % (pathParts.pop(), fullKlass)
        if fullKlass in PYSMELLDICT['CLASSES'].keys():
            break
    else:
        # we don't know about this class, look in the file system
        path, filename = os.path.split(fullPath)
        packages = findRootPackageList(path, filename)
        if packages:
            packagesStr = (".".join(packages)) + "."
        else:
            packagesStr = ""
        fullKlass = "%s%s.%s" % (packagesStr, filename[:-3], klass)
        
    return fullKlass, parents


DELIMITERS = " ()[]{}'\"<>,/-=+*:%^|!@`;"

def getChain(line):
    "get the last chain of property accesses, ie some.thing.other.bother"
    chain = []
    for c in reversed(line):
        if c in DELIMITERS:
            break
        chain.append(c)
    return ''.join(reversed(chain))


class Types(object):
    TOPLEVEL = 'TOPLEVEL'
    FUNCTION = 'FUNCTION'
    METHOD = 'METHOD'
    MODULE = 'MODULE'
    INSTANCE = 'INSTANCE'


class CompletionOptions(object):
    def __init__(self, compType, **kwargs):
        self.compType = compType
        self.extra = kwargs

    def __getattr__(self, item):
        return self.extra[item]
        
    def __eq__(self, other):
        return (isinstance(other, CompletionOptions)
                and self.compType == other.compType and self.extra == other.extra)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return repr(self.compType) + 'with extra: ' + repr(self.extra)
        

def detectCompletionType(fullPath, origSource, lineNo, origCol, base, PYSMELLDICT, update=True):
    """
    Return a CompletionOptions instance describing the type of the completion, along with extra parameters.
    
    args: fullPath -> The full path and filename of the file that is edited
          origSource -> The source of the edited file (it's probably not saved)
          lineNo -> The line number the cursor is in, 1-based
          origCol -> The column number the cursor is in, 0-based
          base -> The string that will be replaced when the completion is inserted
          PYSMELLDICT -> The loaded PYSMELLDICT

    Note that Vim deletes the "base" when a completion is requested so extra trickery must be performed to get it from the source.

    """
    AST = getSafeTree(origSource, lineNo)
    if update:
        currentDict = analyzeFile(fullPath, AST)
        if currentDict is not None:
            updatePySmellDict(PYSMELLDICT, currentDict)
    origLineText = origSource.splitlines()[lineNo - 1] # lineNo is 1 based
    leftSide, rightSide = origLineText[:origCol], origLineText[origCol:]
    leftSideStripped = leftSide.lstrip()

    isImportCompletion = (leftSideStripped.startswith("from ") or leftSideStripped.startswith("import "))
    if isImportCompletion:
        module = leftSideStripped.split(" ")[1]
        if "." in module and " import " not in leftSideStripped:
            module, _ = module.rsplit(".", 1)
        showMembers = False
        if " import " in leftSide:
            showMembers = True
        return CompletionOptions(Types.MODULE, module=module, showMembers=showMembers)

    isAttrLookup = "." in leftSide and not isImportCompletion
    isArgCompletion = base.endswith('(') and leftSide.endswith(base)

    if isArgCompletion:
        rindex = None
        if rightSide.startswith(')'):
            rindex = -1
        funcName = None
        lindex = leftSide.rfind('.') + 1 #rfind will return -1, so with +1 it will be zero
        funcName = leftSide[lindex:-1].lstrip()
        if isAttrLookup:
            return CompletionOptions(Types.METHOD, parents=[], klass=None, name=funcName, rindex=rindex)
        else:
            return CompletionOptions(Types.FUNCTION, name=funcName, rindex=rindex)

    if isAttrLookup and AST is not None:
        var = leftSideStripped[:leftSideStripped.rindex('.')]
        isClassLookup = var == 'self'
        if isClassLookup:
            klass, parents = inferClass(fullPath, AST, lineNo, PYSMELLDICT)
            return CompletionOptions(Types.INSTANCE, klass=klass, parents=parents)
        else:
            chain = getChain(leftSideStripped) # strip dot
            if base and chain.endswith(base):
                chain = chain[:-len(base)]
            if chain.endswith('.'):
                chain = chain[:-1]
            possibleModule = inferModule(chain, AST, lineNo)
            if possibleModule is not None:
                return CompletionOptions(Types.MODULE, module=possibleModule, showMembers=True)
        klass, parents = inferInstance(fullPath, AST, lineNo, var, PYSMELLDICT)
        return CompletionOptions(Types.INSTANCE, klass=klass, parents=parents)
        

    return CompletionOptions(Types.TOPLEVEL)



def findCompletions(base, PYSMELLDICT, options, matcher=None):
    doesMatch = MATCHERS[matcher](base)
    compType = options.compType

    if compType is Types.MODULE:
        completions = _createModuleCompletions(PYSMELLDICT, options.module, options.showMembers)
    elif compType is Types.INSTANCE:
        completions = _createInstanceCompletionList(PYSMELLDICT, options.klass, options.parents)
    elif compType is Types.METHOD:
        completions = _createInstanceCompletionList(PYSMELLDICT, options.klass, options.parents)
        doesMatch = lambda word: word == options.name
    elif compType is Types.FUNCTION:
        completions = [_getCompForFunction(func, 'f') for func in PYSMELLDICT['FUNCTIONS']]
        doesMatch = lambda word: word == options.name
    elif compType is Types.TOPLEVEL:
        completions = _createTopLevelCompletionList(PYSMELLDICT)
        
    if base:
        filteredCompletions = [comp for comp in completions if doesMatch(comp['word'])]
    else:
        filteredCompletions = completions

    filteredCompletions.sort(sortCompletions)

    if filteredCompletions and compType in (Types.METHOD, Types.FUNCTION):
        #return the arg list instead
        oldComp = filteredCompletions[0]
        if oldComp['word'] == options.name:
            oldComp['word'] = oldComp['abbr'][:options.rindex]
    return filteredCompletions


def _createInstanceCompletionList(PYSMELLDICT, klass, parents):
    completions = []
    if klass: #if we know the class
        completions.extend(getCompletionsForClass(klass, parents, PYSMELLDICT))
    else: #just put everything
        for klass, klassDict in PYSMELLDICT['CLASSES'].items():
            addCompletionsForClass(klass, klassDict, completions)
    return completions


def _createTopLevelCompletionList(PYSMELLDICT):
    completions = []
    completions.extend(_getCompForConstant(word) for word in PYSMELLDICT['CONSTANTS'])
    completions.extend(_getCompForFunction(func, 'f') for func in PYSMELLDICT['FUNCTIONS'])
    completions.extend(_getCompForConstructor(klass, klassDict) for (klass, klassDict) in PYSMELLDICT['CLASSES'].items())
    return completions


def _createModuleCompletions(PYSMELLDICT, module, completeModuleMembers):
    completions = []
    splitModules = set()
    for reference in PYSMELLDICT['HIERARCHY']:
        if not reference.startswith(module): continue
        if reference == module: continue

        # like zip, but pad with None
        for mod, ref in map(None, module.split('.'), reference.split('.')):
            if mod != ref:
                splitModules.add(ref)
                break

    if completeModuleMembers:
        members = _createTopLevelCompletionList(PYSMELLDICT)
        completions.extend(comp for comp in members if comp["menu"] == module and not comp["word"].startswith("_"))
        pointers = []
        for pointer in PYSMELLDICT['POINTERS']:
            if pointer.startswith(module) and '.' not in pointer[len(module)+1:]:
                basename = pointer[len(module)+1:]
                if pointer.endswith(".*"):
                    otherModule = PYSMELLDICT['POINTERS'][pointer][:-2] # remove .*
                    completions.extend(_createModuleCompletions(PYSMELLDICT, otherModule, True))
                else:
                    splitModules.add(basename)
                
                
    completions.extend(dict(word=name, kind="t", dup="1") for name in splitModules)
    return completions


def getCompletionsForClass(klass, parents, PYSMELLDICT):
        klassDict = PYSMELLDICT['CLASSES'].get(klass, None)
        completions = []
        ancestorList = []
        nonBuiltinParents = [p for p in parents if not hasattr(__builtin__, p)]
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
        if hasattr(__builtin__, anc): continue
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
