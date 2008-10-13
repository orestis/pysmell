#PySmell

PySmell is a python IDE completion helper. 

It tries to statically analyze Python source code, without executing it,
and generates information about a project's structure that IDE tools can
use.

The first target is Vim, because that's what I'm using and because its
completion mechanism is very straightforward.

##Download and Installation

PySmell's code is available at
[GitHub](http://github.com/orestis/pysmell/tree/v0.6). You can click
'Download' to get it as a zip/tar if you don't have git installed.

Extract and drop the pysmell package somewhere in your `PYTHONPATH`.
Distutils support coming soon - patches welcome!

##Usage

To generate a PYSMELLTAGS file, use:

    cd /root/of/project /dir/of/pysmell.py .

If you want to specifically include or exclude some files or directories
(eg. tests), you can use: 

    /dir/of/pysmell.py [Package Package File File ...] [-x Excluded Excluded ...]

Check for more options by invoking `pysmell.py` without any arguments

##Using external libraries

PySmell can handle completions of external libraries, like the Standard
Library and Django. 

To use external libraries, you have to first analyze the libraries you
want, eg. for stdlib:

    pysmell.py . -x site-packages test -o ~/PYSMELLTAGS.stdlib

This will create PYSMELLTAGS.stdlib in your HOME. Copy that in the root
of your project, and repeat for other libraries by changing the
extension. Note that you still have to have a root PYSMELLTAGS file with
no extension at the very root of your project.

##Partial tags

Sometimes it's useful to not pollute global namespaces with tags of
sub-projects. For example, assume that there is a Tests package, which
has hundreds of tests, together with a few testing-related modules. You
only want to see these completions when working on test file.

To accomplish that, you can put PYSMELLTAGS.* files inside
subdirectories, and they will be used only when you're working on a file
somewhere in that directory or its children.

    /dir/of/pysmell.py Tests/FunctionalTest.py Tests/UndoTestCase.py -o Tests/PYSMELLTAGS.Tests

The information in FunctionalTest and UndoTestCase will only be
accessible when editing a file inside the Tests package.

##Vim

To use PySmell omnicompletion from inside Vim, you have to have:

1. Python support 
2. The pysmell package in your PYTHONPATH (sometimes
Vim is silly about this) 
3. Source pysmell/pysmell.vim 
4. `:set omnifunc=pysmell#Complete` Note: If you want to always use pysmell for
python, do: `autocmd FileType python set omnifunc=pysmell#Complete`
5. [OPTIONAL] Select a matcher of your liking - look at pysmell.vim for
options. Eg: `:let g:pysmell_matcher='camel-case'`

You can then use ^X^O to invoke Vim's omnicompletion.

You can generate debugging information by doing:

    :let g:pysmell_debug=1
    :e PYSMELL_DEBUG

Debug information will be appended in that buffer, copy and paste it
into an email.

##Reporting issues

Look in the [TODO](http://github.com/orestis/pysmell/wikis/todo) first.
Vote up on issues that you feel strongly about!

Send me an email at orestis@orestis.gr. If you can create a unit test
that exposes that behaviour, it'd be great!
