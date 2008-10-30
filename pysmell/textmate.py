import os
import sys
from pysmell import idehelper, vimhelper
from pysmell import tags as tags_module

sys.path.append(os.environ['TM_SUPPORT_PATH'] + '/lib')
import dialog

def write(word):
    sys.stdout.write(word)


def tags(projectDir):
    args = ['pysmell', projectDir, '-o', os.path.join(projectDir, 'PYSMELLTAGS')]
    sys.argv = args
    tags_module.main()
    write('PYSMELLTAGS created in %s' % projectDir)


def main():
    cur_file = os.environ.get("TM_FILEPATH")
    source = sys.stdin.read()
    line_no = int(os.environ.get("TM_LINE_NUMBER"))
    cur_col = int(os.environ.get("TM_LINE_INDEX"))

    PYSMELLDICT = idehelper.findPYSMELLDICT(cur_file)
    line = source.splitlines()[line_no - 1]
    index = vimhelper.findBase(line, cur_col)
    base = line[index:cur_col]

    options = idehelper.detectCompletionType(cur_file, source, line_no, cur_col, base, PYSMELLDICT)
    completions = idehelper.findCompletions(base, PYSMELLDICT, options)

    if not completions:
        write('No completions found')
        sys.exit(206) #magic code for tooltip
    if len(completions) == 1:
        new_word = completions[0]['word']
        write(new_word)
    elif len(completions) > 1:
        dialogTuples = [
            (
              "%s - %s" % (comp.get('abbr', comp['word']), comp.get('menu', '')),
              index)
            for index, comp in enumerate(completions)
        ]
        compIndex = dialog.menu(dialogTuples)
        if compIndex is not None:
            write(completions[compIndex]['word'])

