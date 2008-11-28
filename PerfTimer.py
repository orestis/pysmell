from datetime import datetime
import sys

OUT = sys.stdout

class PerfTimer(object):
    def __init__(self, name, indent=0):
        self.name = ('  ' * indent) + name
        self.points = []
        self.add('start')

    def add(self, name):
        self.points.append((name, datetime.now()))
        if len(self.points) > 1:
            self.report(self.points[-2], self.points[-1])

    def report(self, (startName, startTime), (endName, endTime)):
        print >> OUT, '%s: from %s to %s: %0.3f' % (self.name, startName, endName,
            (endTime - startTime).microseconds / 1000.0)
        OUT.flush()

    def _end(self):
        self.add('end')
        self.report(self.points[0], self.points[-1])

    def __getattr__(self, name):
        if name == 'end':
            self._end()
        else:
            self.add(name)
