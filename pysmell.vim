
if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

function! pysmell#Complete(findstart, base)
    "findstart = 1 when we need to get the text length
    if a:findstart == 1
python << eopython
import vim
row, col = vim.current.window.cursor
line = vim.current.buffer[row-1]
found = False
while col > 1:
    col -= 1
    if line[col] in '. (':
        found = True
        vim.command("return %d" % (col+1))
        break
if not found:
    vim.command("return 0")
eopython
    "findstart = 0 when we need to return the list of completions
    else
        "vim no longer moves the cursor upon completion... fix that
        let line = getline('.')
        let idx = col('.')
        let cword = ''
        while idx > 0
            let idx -= 1
            let c = line[idx]
            if c =~ '\w' || c =~ '\.' || c == '('
                let cword = c . cword
                continue
            elseif strlen(cword) > 0 || idx == 0
                break
            endif
        endwhile
        let g:pysmell_args = 0
        let g:pysmell_completions = [] 
        execute "python vimcomplete('" . cword . "', '" . a:base . "')"
        return g:pysmell_completions
    endif
endfunction

python << eopython
def vimcomplete(cword, base):
    import vim, os
    vim.command('let g:pysmell_completions = []')
    filename = vim.current.buffer.name
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
    completions = []
    for module, moduleDict in PYSMELLDICT.items():
        completions.extend([{'word': word, 'kind': 'd', 'menu': module} for word in moduleDict['CONSTANTS']])
        completions.extend([getCompForFunction(func, module) for func in moduleDict['FUNCTIONS']])
        for klass, klassDict in moduleDict['CLASSES'].items():
            completions.append(dict(word=klass, kind='t', abbr='%s(%s)' % (klass, _argsList(klassDict['constructor']))))
            completions.extend([dict(word=word, kind='m', menu='%s:%s' % (module, klass)) for word in klassDict['properties']])
            completions.extend([getCompForFunction(func, '%s:%s' % (module, klass)) for func in klassDict['methods']])
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
            vim.command('let g:pysmell_args = %d' % diff)
    output = repr(filteredCompletions)
    vim.command('let g:pysmell_completions = %s' % (output, ))

def getCompForFunction(func, menu):
    return dict(word=func[0], kind='f', menu=menu,
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
eopython
set omnifunc=pysmell#Complete
