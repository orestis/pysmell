from pysmell import idehelper
import asynchat, asyncore, socket

class server(asyncore.dispatcher):

    def __init__ (self, port):
        asyncore.dispatcher.__init__ (self)
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        here = ('127.0.0.1', port + 8000)
        self.bind(here)
        self.listen(5)
 
    def handle_accept (self):
        conn, addr = self.accept()
        project_manager(conn, addr)

class states(object):
    WAITING_SOURCE = object()
    WAITING_CURSOR = object()
    IDLE = object()


class project_manager(asynchat.async_chat):
    def __init__ (self, conn, addr):
        asynchat.async_chat.__init__ (self, conn)
        self.terminator = '\x00\xDE\xAD\xBE\xEF\x00'
        self.set_terminator(self.terminator)
        self.buffer = []
        self.state = states.IDLE
        self.projectPath = None
        self.pysmellDict = None
        self.source = None
        self.filePath = None

 
    def collect_incoming_data (self, data):
        self.buffer.append(data)
     
 
    def respond(self, data):
        self.push(data)
        self.push(self.terminator)
    
 
    def found_terminator (self):
        data = ''.join(self.buffer)
        self.buffer = []
        if self.state is states.IDLE:
            #data is the filepath
            self.filePath = data
            if self.pysmellDict is None:
                PYSMELLDICT, project = idehelper.findPYSMELLDICT(self.filePath)
                if PYSMELLDICT is None:
                    self.respond("NO PYSMELLTAGS")
                    return
                self.projectPath = project
                self.pysmellDict = PYSMELLDICT
            self.state = states.WAITING_SOURCE
            self.respond('SEND SOURCE')
        elif self.state is states.WAITING_SOURCE:
            #data is the source
            self.source = data
            self.state = states.WAITING_CURSOR
            self.respond('SEND CURSOR')
        elif self.state is states.WAITING_CURSOR:
            #data is lineno, col, base
            lineno, col, base = data.split(',')
            options = idehelper.detectCompletionType(
                self.filePath, self.source, int(lineno), int(col), base, self.pysmellDict)
            print options
            completions = idehelper.findCompletions(base, self.pysmellDict, options)
            self.state = states.IDLE
            self.respond(repr(completions))
        else:
            raise ValueError('Invalid state')
 

    def handle_close(self):
        print 'Closing'
        self.close()
 
if __name__ == '__main__':
   ps = server(80)
   asyncore.loop()

