import inspect
from inspect import joinseq, strseq

from pysmell.codefinder import ModuleDict

def _formatval(arg):
    if inspect.isroutine(arg) or inspect.isclass(arg):
        return "=" + arg.__name__
    else:
        return "=" + repr(arg)


#override formatargspec to return list rather than string
def formatargspec(args, varargs=None, varkw=None, defaults=None):
    formatarg=str
    formatvarargs=lambda name: '*' + name
    formatvarkw=lambda name: '**' + name
    formatvalue=_formatval
    specs = []
    if defaults:
        firstdefault = len(args) - len(defaults)
    for i in range(len(args)):
        spec = strseq(args[i], formatarg, joinseq)
        if defaults and i >= firstdefault:
            spec = spec + formatvalue(defaults[i - firstdefault])
        specs.append(spec)
    if varargs is not None:
        specs.append(formatvarargs(varargs))
    if varkw is not None:
        specs.append(formatvarkw(varkw))
    return specs

skip_modules = set()
def get_dynamic_tags(module, visited_modules=None):
    if visited_modules == None:
        visited_modules = set()
    mod = __import__(module)
    print 'dynamic tags of', module
    visited_modules.add(module)
    attrs = [a for a in dir(mod) if not a.startswith('__')]
    pysmelld = ModuleDict()
    pysmelld['HIERARCHY'].append(module)
    for attr in attrs:
        o = getattr(mod, attr)
        if hasattr(o, '__module__') and o.__module__ != module:
            pysmelld['POINTERS']['%s.%s' % (module, attr)] = '%s.%s' % (o.__module__, attr)
            continue
        if inspect.isroutine(o):
            _add_function(mod, o, pysmelld)
        elif inspect.isclass(o):
            _add_class(o, pysmelld)
        elif inspect.ismodule(o) and attr in skip_modules and attr in visited_modules:
            pysmelld.update(get_dynamic_tags(o.__name__, visited_modules))
        else:
            # Assume it's a constant.
            _add_constant(mod, attr, pysmelld)
    return pysmelld


def _add_function(m, o, pysmelld):
    '''Add the function `o` to the pysmelld dictionary.

    m: Module containing the function o.
    o: Function object to add to the pysmelld dictionary.
    pysmelld: the pysmell dictionary.

    returns: None.
    '''
    # I'm not sure how to get the function arguments / defaults for builtins.
    fname = '%s.%s' % (m.__name__, o.__name__)
    argspec = inspect.getargspec(o)
    args = formatargspec(*argspec)
    docs = inspect.getdoc(o)
    pysmelld['FUNCTIONS'].append((fname, args, docs))

def _add_class(o, pysmelld):
    '''Add the class `o` to the pysmelld dictionary.

    o: Function object to add to the pysmelld dictionary.
    pysmelld: the pysmell dictionary.

    returns: None.
    '''
    # For builtin classes, the easy thing to do is just store the class.
    cname = '%s.%s' % (o.__module__, o.__name__)
    if hasattr(o, '__init__'):
        argspec = inspect.getargspec(o.__init__)
        args = formatargspec(*argspec)[1:] #remove self
    else:
        args = []

    classd = {'bases': [],
              'constructor': args,
              'docstring': inspect.getdoc(o),
              'methods': [],
              'properties': [] }
    pysmelld['CLASSES'][cname] = classd


def _add_constant(mod, const, pysmelld):
    '''Add a constant to the pysmelld dictionary from module m.

    mod: Module containing the constant const.
    const: Name of the constant being added.
    pysmelld: the pysmell dictionary.

    returns: None.
    '''
    pysmelld['CONSTANTS'].append('%s.%s' % (mod.__name__, const))


