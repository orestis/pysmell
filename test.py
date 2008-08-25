class Dog(object):
    def __init__(self, name):
        self.name = name

    def bark(self):
        print 'woof'

class Cat(object):
    def __init__(self, name):
        self.name = name

    def pout(self):
        print 'meow'


def garden(spot, bill):
    print spot.name
    print bill.name
    spot.bark()
    bill.pout()

garden()
