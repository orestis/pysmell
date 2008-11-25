" pysmell.vim
" Omnicompletions provider for Python, using PYSMELLTAGS files
" Copyright (C) 2008 Orestis Markou
" All rights reserved
" E-mail: orestis@orestis.gr

" pysmell v0.7.2
" http://orestis.gr

" Released subject to the BSD License 

" Options:
"   g:pysmell_debug : set to 1 and create a PYSMELL_DEBUG buffer. Info will get appended there.
"   g:pysmell_matcher : one of the following, listed from stricter to fuzzier:
"        'case-sensitive'
"        'case-insensitive'     "default
"        'camel-case'
"        'camel-case-sensitive'
"        'smartass'
"        'fuzzy-ci'
"        'fuzzy-cs'
                

if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

if !exists('g:pysmell_debug')
    let g:pysmell_debug = 0
endif
if !exists('g:pysmell_matcher')
    let g:pysmell_matcher='case-insensitive'
endif

python << eopython
from pysmell import vimhelper, idehelper
import vim
import string
from PerfTimer import PerfTimer

TRANSLATEQUOTES = string.maketrans("\'\"", "\"\'")
eopython

function! pysmell#Complete(findstart, base)
    "findstart = 1 when we need to get the text length
    if a:findstart == 1
python << eopython
row, col = vim.current.window.cursor
line = vim.current.buffer[row-1]
index = idehelper.findBase(line, col)
vim.command('let g:pysmell_origCol = %d' % col)
vim.command('return %d' % index)
eopython
    "findstart = 0 when we need to return the list of completions
    else
        let g:pysmell_args = 0
        let g:pysmell_completions = [] 
python << eopython
origCol = int(vim.eval('g:pysmell_origCol'))
origSource = '\n'.join(vim.current.buffer)
vimcompletePYSMELL(origSource, vim.current.window.cursor[0], origCol, vim.eval("a:base"))

eopython
        return g:pysmell_completions
    endif
endfunction

python << eopython
def vimcompletePYSMELL(origSource, origLineNo, origCol, base):
    import PerfTimer as PTModule
    PTModule.OUT = file('perflog.txt', 'w')
    t = PerfTimer('complete')
    fullPath = vim.current.buffer.name
    t.BeforeFind
    PYSMELLDICT = idehelper.findPYSMELLDICT(fullPath)
    t.AfterFind
    if not PYSMELLDICT:
        vim.command("echoerr 'No PYSMELLTAGS found. You have to generate one.'")
        return

    t.BeforeDetection
    options = idehelper.detectCompletionType(fullPath, origSource, origLineNo, origCol, base, PYSMELLDICT)
    t.AfterDetection
    if int(vim.eval('g:pysmell_debug')):
        for b in vim.buffers:
            if b.name.endswith('PYSMELL_DEBUG'):
                b.append("%s %s %s %s %s" % (fullPath, origSource[origLineNo], origCol, base))
                b.append("%r" % (options,))
                break

    t.BeforeCompletions
    completions = idehelper.findCompletions(base, PYSMELLDICT, options, vim.eval('g:pysmell_matcher'))
    t.AfterCompletions
    output = repr(completions)
    t.AfterOutput
    translated = output.translate(TRANSLATEQUOTES)
    t.AfterTranslate
    vim.command('let g:pysmell_completions = %s' % (translated, ))
    t.end
    PTModule.OUT.close()

eopython
