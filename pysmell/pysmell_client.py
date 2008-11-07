import asyncore, asynchat, socket

class client(asynchat.async_chat):

    def __init__(self, filepath, source, line, col, base):
        asynchat.async_chat.__init__(self)
        self.filepath = filepath
        self.source = source
        self.line = line
        self.col = col
        self.base = base
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.terminator = '\x00\xDE\xAD\xBE\xEF\x00'
        self.set_terminator(self.terminator)
        self.buffer = []
        self.completions = None
        self.connect( ('127.0.0.1', 8080) )


    def respond(self, data):
        self.push(data)
        self.push(self.terminator)
 

    def handle_connect(self):
        self.respond(self.filepath)
 
 
    def handle_expt(self):
        if not self.connected:
            self.close()
 
 
    def collect_incoming_data (self, data):
        self.buffer.append(data)
 
 
    def found_terminator (self):
        data = ''.join(self.buffer)
        self.buffer = []
        if data == 'NO PYSMELLTAGS':
            self.close()
        elif data == 'SEND SOURCE':
            self.respond(self.source)
        elif data == 'SEND CURSOR':
            self.respond('%s,%s,%s' % (self.line, self.col, self.base))
        else:
            #data is completions
            self.completions = eval(data) #holy security breach, batman!
            self.close()


if __name__ == '__main__':
   c = http_client()
   asyncore.loop()

