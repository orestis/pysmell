
if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

python << eopython
import sys
sys.path.append('/Users/orestis/Developer')
from pysmell import vimhelper
import vim
eopython

function! pysmell#Complete(findstart, base)
    "findstart = 1 when we need to get the text length
    if a:findstart == 1
python << eopython
index = vimhelper.findBase(vim)
vim.command('return %d' % index)
eopython
    "findstart = 0 when we need to return the list of completions
    else
        let g:pysmell_args = 0
        let g:pysmell_completions = [] 
python << eopython
cword = vimhelper.findWord(vim)
vim.command('let cword = %r' % cword)
eopython
        execute "python vimcomplete('" . cword . "', '" . a:base . "')"
        return g:pysmell_completions
    endif
endfunction

python << eopython
def vimcomplete(cword, base):
    vim.command('let g:pysmell_completions = []')
    filename = vim.current.buffer.name
    PYSMELLDICT = vimhelper.findPYSMELLDICT(filename)
    completions = vimhelper.findCompletions(cword, base, PYSMELLDICT)
    output = repr(completions)
    vim.command('let g:pysmell_completions = %s' % (output, ))

eopython
set omnifunc=pysmell#Complete
