
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
    if line[col] == '.' or line[col] == ' ':
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
    while not os.path.exists(os.path.join(directory, 'PYSMELLTAGS')):
        directory, _ = os.path.split(directory)
    tagsFile = os.path.join(directory, 'PYSMELLTAGS')
    PYSMELLDICT = eval(file(tagsFile).read())
    completions = []
    for module, moduleDict in PYSMELLDICT.items():
        completions.extend([{'word': word, 'kind': 't', 'menu': module} for word in moduleDict['CONSTANTS']])
        completions.extend([{'word': info[0], 'kind': 'f', 'menu': module,
                            'abbr': '%s(%s)' % (info[0], ', '.join([str(sth) for sth in info[1]]))} for info in
                            moduleDict['FUNCTIONS']])
        for klass, klassDict in moduleDict['CLASSES'].items():
            completions.extend(dict(word=word, kind='m', menu='%s.%s' % (module, klass)) for word in klassDict['properties'])
            completions.extend([{'word': info[0], 'kind': 'f', 'menu': '%s.%s' % (module, klass),
                                'abbr': '%s(%s)' % (info[0], ', '.join([str(sth) for sth in info[1]]))} for info in
                                klassDict['methods']])
    if base:
        filteredCompletions = [comp for comp in completions if
                                (isinstance(comp, basestring) and comp.startswith(base)) or
                                (isinstance(comp, dict) and comp['word'].startswith(base))]
    else:
        filteredCompletions = completions
    filteredCompletions.sort()
    output = repr(filteredCompletions)
    vim.command('let g:pysmell_completions = %s' % (output, ))
eopython
set omnifunc=pysmell#Complete
