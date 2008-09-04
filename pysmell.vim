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

python << eopython
from pysmell import vimhelper
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
vimcompletePYSMELL(origLine, origCol, vim.eval("a:base"))

eopython
        return g:pysmell_completions
    endif
endfunction

python << eopython
def vimcompletePYSMELL(origLine, origCol, base):
    vim.command('let g:pysmell_completions = []')
    filename = vim.current.buffer.name
    PYSMELLDICT = vimhelper.findPYSMELLDICT(filename)
    completions = vimhelper.findCompletions(vim, origLine, int(origCol), base, PYSMELLDICT)
    output = repr(completions)
    vim.command('let g:pysmell_completions = %s' % (output, ))

eopython
let g:pysmell_matcher='case-insensitive'
