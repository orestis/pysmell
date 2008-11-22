#PySmell

PySmell is a python IDE completion helper. 

It tries to statically analyze Python source code, without executing it,
and generates information about a project's structure that IDE tools can
use.

There is currently support for Vim, Emacs and TextMate. Feel free to contribute
your own favourite editor bindings, or to improve the existing ones.

##Download and Installation

PySmell is available at [PyPI](http://pypi.python.org/pypi/pysmell). The best
way to install PySmell is by downloading the source distribution and doing
`python setup.py install`. While `easy_install pysmell` also works, I haven't
yet found a way of distributing the editor scripts with it (suggestions welcome).

You should be able to `import pysmell` inside your Python interpreter and invoke
`pysmell` at the command line.

You can track the development of PySmell by visiting 
[GitHub](http://github.com/orestis/pysmell/). You can click 'Download'
to get it as a zip/tar if you don't have git installed. `python setup.py
develop` will setup your enviroment.

##Usage

Before you invoke PySmell, you need to generate a PYSMELLTAGS file: 

    cd /root/of/project
    pysmell .

If you want to specifically include or exclude some files or directories
(eg. tests), you can use: 

    pysmell [Package Package File File ...] [-x Excluded Excluded ...]

Check for more options by invoking `pysmell` without any arguments

##Using external libraries

PySmell can handle completions of external libraries, like the Standard
Library and Django. 

To use external libraries, you have to first analyze the libraries you
want, eg. for stdlib:

    pysmell . -x site-packages test -o ~/PYSMELLTAGS.stdlib

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

    pysmell Tests/FunctionalTest.py Tests/UndoTestCase.py -o Tests/PYSMELLTAGS.Tests

The information in FunctionalTest and UndoTestCase will only be
accessible when editing a file inside the Tests package.

##Vim

To use PySmell omnicompletion from inside Vim, you have to have:

1. Python support in vim (`:echo has('python')`)
2. The pysmell package in the PYTHONPATH that Vim uses: `python import pysmell` should work.
3. Drop pysmell.vim in ~/.vim/plugin
4. `:setlocal omnifunc=pysmell#Complete` Note: If you want to always use pysmell for
python, do: `autocmd FileType python setlocal omnifunc=pysmell#Complete`
5. [OPTIONAL] Select a matcher of your liking - look at pysmell.vim for
options. Eg: `:let g:pysmell_matcher='camel-case'`

You can then use ^X^O to invoke Vim's omnicompletion.

You can generate debugging information by doing:

    :let g:pysmell_debug=1
    :e PYSMELL_DEBUG

Debug information will be appended in that buffer, copy and paste it
into the report.

##TextMate

Double-click PySmell.tmbundle :)

Complete with alt-esc - look into the bundle for more commands.

You can find the bundle in the source distribution - it's not installed
with the egg, because it's too much trouble. 

Set TM_PYTHON in your Shell Variables to point to the Python where you
installed PySmell.

##Emacs

Put pysmell.el into your `load-path`, and inside your .emacs file put:

    (require 'pysmell)
    (add-hook 'python-mode-hook (lambda () (pysmell-mode 1)))

Complete with M-/, create tags with M-x pysmell-make-tags

[Pymacs](http://pymacs.progiciels-bpi.ca/) is required as well.

##Reporting issues

PySmell is hosted at [Google Code](http://code.google.com/p/pysmell).

Look in the [issues list](http://code.google.com/p/pysmell/issues) first.
Star issues that you feel strongly about, or create your own.

If you can create a unit test that exposes that behaviour, it'd be great!
