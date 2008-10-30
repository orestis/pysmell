from pysmell import idehelper
from re import split


def _uniquify(l):
    found = set()
    for item in l:
        if item not in found:
            yield item
        found.add(item)


def get_completions(fullPath, origSource, lineNo, origCol, matcher):
    """arguments: fullPath, origSource, lineNo, origCol, matcher

When visiting the file at fullPath, with edited source origSource, find a list 
of possible completion strings for the symbol located at origCol on orgLineNo using 
matching mode matcher"""
    PYSMELLDICT = idehelper.findPYSMELLDICT(fullPath)
    if not PYSMELLDICT:
        return
    origLine = origSource.splitlines()[lineNo - 1]
    base = split("[,.\-+/|\[\]]", origLine[:origCol].strip())[-1]
    options = idehelper.detectCompletionType(fullPath, origSource, lineNo, origCol, base, PYSMELLDICT)
    completions = [completion['word'] for completion in idehelper.findCompletions(base, PYSMELLDICT, options, matcher)]
    completions = list(_uniquify(completions))
    return completions




        
