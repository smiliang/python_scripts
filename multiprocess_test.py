import multiprocessing, select, sys, os

def write(s):
    print(f'before {hex(id(s))}')
    s += 5
    print(f'child value {s}')
    print(f'after {hex(id(s))}')    

def directtest():
    test = 5
    print(hex(id(test)))
    
    p = multiprocessing.Process(target=write, args=((test,)))
    
    p.start()
    p.join()
    
    print(f'father addr {hex(id(test))}')        
    print(f'father value {test}')

#----------------------------------------------------------------------
def writepipe(p):
    receiveCache = []
    running = True
    while running:
        readable, writeable, exeptions = select.select([p],[p],[])
        for read in readable:
            data = read.recv()
            print(f'data {data}, addr {hex(id(data))}')
            receiveCache.append(data)
            if data == b'\n':
                running = False
        for wr in writeable:
            if receiveCache:
                wr.send(receiveCache.pop())

def pipetest():
    parent_conn, child_conn = multiprocessing.Pipe()
    p = multiprocessing.Process(target=writepipe, args=(child_conn,))
    p.start()
    running = True
    sendCache = []
    while running:
        readable, writeable, exceptions = select.select([parent_conn, sys.stdin], [parent_conn], [])
        for read in readable:
            if read == parent_conn:
                data = read.recv()
                print(f'data back {data}, addr {hex(id(data))}')
                if data == b'\n':
                    running = False
            elif read == sys.stdin:
                data = read.readline().encode('utf-8')
                print(f'stdin data {data}, addr {hex(id(data))}')
                sendCache.append(data)
        for wr in writeable:
            if sendCache:
                wr.send(sendCache.pop())

#----------------------------------------------------------------------
def writequeue(q):
    receiveCache = []
    running = True
    while running:
        readable, writeable, exeptions = select.select([q._reader],[q._writer],[])
        for read in readable:
            data = q.get()
            print(f'data {data}, addr {hex(id(data))}, pid {os.getpid()}')
            receiveCache.append(data)
            if data == b'\n':
                running = False
        for wr in writeable:
            if receiveCache:
                q.put(receiveCache.pop()+b' '+str(os.getpid()).encode('utf-8'))

def queuetest():
    queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target = writequeue, args = (queue,))
    p2 = multiprocessing.Process(target = writequeue, args = (queue,))    
    p1.start()
    p2.start()
    running = True
    sendCache = []
    while running:
        readable, writeable, exceptions = select.select([queue._reader, sys.stdin], [queue._writer], [])
        for read in readable:
            if read == queue._reader:
                data = queue.get()
                print(f'data back {data}, addr {hex(id(data))}, pid {os.getpid()}')
                if data == b'\n':
                    running = False
            elif read == sys.stdin:
                data = read.readline().encode('utf-8')
                print(f'stdin data {data}, addr {hex(id(data))}')
                sendCache.append(data)
        for wr in writeable:
            if sendCache:
                queue.put(sendCache.pop())    

if __name__ == "__main__":
    #directtest()
    #pipetest()
    queuetest()