
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
        "execute "python vimcomplete('" . cword . "', '" . a:base . "')"
        return ['test']
    endif
endfunction
