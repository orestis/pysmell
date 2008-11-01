
Q
function ReportException(message)
    if a:message == ""
        execute "!echo Exception: " . v:exception . " >> vimtest.out"
    else
        execute "!echo Exception: " . a:message . " >> vimtest.out"
    endif
    execute "cq!"
endfun
function InsertText(text)
    :execute "normal a". a:text ."\<Esc>"
endfun
function InsertLine(line)
    :execute "normal o". a:line ."\<Esc>"
endfun
try
    source pysmell.vim
catch
    call ReportException("could not load pysmell.vim")
endtry
visual
:try
    :e TestData/test.py
    :set omnifunc=pysmell#Complete
    :set cot=
    :call InsertText("from PackageA.ModuleA import ClassA")
    :call InsertLine("o = ClassA()")
    :call InsertLine("")
    :call InsertText("o.")
    :w

:catch
    :call ReportException()
:endtry
:q!
