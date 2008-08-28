def TopLevelFunction(arg1, arg2):
    class InnerClassB(object):
        def anotherMethod(self, c):
            pass
    return 'something'

CONSTANT = 123

class ClassA(object):
    classPropertyA = 4
    classPropertyB = 5

    def __init__(self):
        self.propertyA = 1
        self.propertyB = 2


    @property
    def propertyC(self):
        return 3

    def methodA(self, argA, argB, *args, **kwargs):
        self.propertyD = 4
        class InnerClass(object):
            def innerClassMethod(self):
                self.aHiddenProperty = 'dont bother with inner classes'
                pass
        def innerFunction(sth, sthelse):
            return 'result'
        return 'A'


class ChildClassA(ClassA, object):
    'a class docstring, imagine that'
    def __init__(self, conArg):
        self.extraProperty = 45

    def extraMethod(self):
        "i have a docstring"
        pass
