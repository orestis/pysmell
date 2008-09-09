" pysmell.vim
" Omnicompletions provider for Python, using PYSMELLTAGS files
" Copyright (C) 2008 Orestis Markou
" All rights reserved
" E-mail: orestis@orestis.gr

" pysmell v0.2
" http://orestis.gr

" Released subject to the BSD License 

if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

let g:pysmell_debug = 0
let g:pysmell_matcher='case-insensitive'

python << eopython
from pysmell import vimhelper, idehelper
import vim
eopython

function! pysmell#Complete(findstart, base)
    "findstart = 1 when we need to get the text length
    if a:findstart == 1
python << eopython
row, col = vim.current.window.cursor
vim.command('let g:pysmell_origCol = %d' % col)
vim.command('let g:pysmell_origLine = %r' % vim.current.buffer[row-1])
index = vimhelper.findBase(vim)
vim.command('return %d' % index)
eopython
    "findstart = 0 when we need to return the list of completions
    else
        let g:pysmell_args = 0
        let g:pysmell_completions = [] 
python << eopython
origCol = int(vim.eval('g:pysmell_origCol'))
origLine = vim.eval('g:pysmell_origLine')
origSource = '\n'.join(vim.current.buffer)
vimcompletePYSMELL(origSource, origLine, vim.current.window.cursor[0], origCol, vim.eval("a:base"))

eopython
        return g:pysmell_completions
    endif
endfunction

python << eopython
def vimcompletePYSMELL(origSource, origLineText, origLineNo, origCol, base):
    vim.command('let g:pysmell_completions = []')
    fullPath = vim.current.buffer.name
    PYSMELLDICT = idehelper.findPYSMELLDICT(fullPath)

    if int(vim.eval('g:pysmell_debug')):
        for b in vim.buffers:
            if b.name.endswith('PYSMELL_DEBUG'):
                b.append("%s %s %s %s %s" % (fullPath, origLineText, origLineNo, origCol, base))
                break

    options = idehelper.detectCompletionType(fullPath, origSource, origLineText, origLineNo, origCol, base, PYSMELLDICT)
    completions = idehelper.findCompletions(base, PYSMELLDICT, options, vim.eval('g:pysmell_matcher'))
    output = repr(completions)
    vim.command('let g:pysmell_completions = %s' % (output, ))

eopython
