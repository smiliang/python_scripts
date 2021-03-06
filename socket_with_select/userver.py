import socket
import select
import sys
import os
import multiprocessing

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
sock.bind(('127.0.0.1', 8001))

writeCache = []

#----------------------------------------------------------------------
def selectMode(server = sock):
    print('select Mode')
    inputs = [server,]
    outputs = [server,]
    sendCache = []
    running = True
    while running:
        try:
            readable, writeable, exceptions = select.select(inputs, outputs, [])
        except Exception as e:
            print(e)
        
        for read in readable:
            if read == sys.stdin:
                junk = sys.stdin.readline()
                running = False
                inputs.clear()
                outputs.clear()
                break
            elif read == server:
                try:
                    data, addr = server.recvfrom(1024)
                    print(f'receive {data} from {addr} pid {os.getpid()}')
                    sendCache.append(addr)
                    sendCache.append(data)                    
                except (OSError, IOError) as e:
                    print(f'no gained, pid {os.getpid()} err {e}')
            else:
                print(f'unkown read {read}')
        for write in writeable:
            if write == server:
                if sendCache:
                    server.sendto(sendCache.pop(), sendCache.pop())
            else:
                print(f'unkown write {write}')
    server.close()
    
#----------------------------------------------------------------------
def pollMode():
    print('poll Mode')
    running = True
    poll = select.poll()
    poll.register(sock.fileno(), select.POLLIN | select.POLLOUT)
    poll.register(sys.stdin.fileno(), select.POLLIN)
    while running:
        try:
            events = poll.poll()
        except Exception as e:
            print(e)
        for fileno, event in events:
            if fileno == sock.fileno():
                if event & select.POLLIN:
                    data, addr = sock.recvfrom(1024)
                    print(f'receive from {addr} data {data}')
                    writeCache.append(addr)
                    writeCache.append(data)
                elif event & select.POLLOUT:
                    if writeCache:
                        sock.sendto(writeCache.pop(), writeCache.pop())
                else:
                    print(f'unknow event for sock {event}')
            elif fileno == sys.stdin.fileno():
                if event & select.POLLIN:
                    junk = sys.stdin.readline()
                    running = False
                    poll.unregister(sock.fileno())
                    poll.unregister(sys.stdin.fileno())
                    break
                else:
                    print(f'unknown event for stdin {event}')
            else:
                print(f'unknow fileno {fileno} event {event}')
    sock.close()

#----------------------------------------------------------------------
def kqueueMode():
    print('kqueue Mode')
    running = True
    kq = select.kqueue()
    kq.control([select.kevent(sock.fileno(), select.KQ_FILTER_READ, select.KQ_EV_ADD)], 0)
    kq.control([select.kevent(sock.fileno(), select.KQ_FILTER_WRITE, select.KQ_EV_ADD)], 0)    
    kq.control([select.kevent(sys.stdin.fileno(), select.KQ_FILTER_READ, select.KQ_EV_ADD)], 0)
    while running:
        try:
            events = kq.control(None, 1024)
        except Exception as e:
            print(e)
        for each in events:
            if each.ident == sock.fileno():
                if each.flags & select.KQ_EV_ADD and each.filter == select.KQ_FILTER_READ:
                    data, addr = sock.recvfrom(1024)
                    print(f'receive from {addr} data {data}')
                    writeCache.append(addr)
                    writeCache.append(data)
                elif each.flags & select.KQ_EV_ADD and each.filter == select.KQ_FILTER_WRITE:
                    if writeCache:
                        sock.sendto(writeCache.pop(), writeCache.pop())
                else:
                    print(f'unkown sock event {each.flags} {each.filter}')
            elif each.ident == sys.stdin.fileno():
                if each.flags & select.KQ_EV_ADD and each.filter == select.KQ_FILTER_READ:
                    junk = sys.stdin.readline()
                    running = False
                    kq.control([select.kevent(sock.fileno(), select.KQ_FILTER_READ, select.KQ_EV_DELETE)],0)
                    kq.control([select.kevent(sock.fileno(), select.KQ_FILTER_WRITE, select.KQ_EV_DELETE)],0)                    
                    kq.control([select.kevent(sys.stdin.fileno(), select.KQ_FILTER_READ, select.KQ_EV_DELETE)], 0)
                    break
                else:
                    print(f'unkown stdin {each.ident} {each.flags} {each.filter}')
            else:
                print(f'unkown each {each.ident} {each.flags} {each.filter}')
    sock.close()

if __name__ == '__main__':
    #selectMode()
    #pollMode()
    #kqueueMode()
    
    '''
    childs = []
    isc = False
    for i in range(3):
        pid = os.fork()
        if 0 == pid:
            selectMode()
            print(f"{os.getpid()} (child) just was created by {os.getppid()}. i {i}")
            isc = True
            break
        else:
            print(f"{os.getpid()} (parent) just created {pid}. i {i}")
            childs.append(pid)

    if not isc:
        print(f'childs {childs}')
        for pid in childs:
            os.waitpid(pid, 0)
    '''
    
    p1 = multiprocessing.Process(target = selectMode, args = (sock,))
    p2 = multiprocessing.Process(target = selectMode, args = (sock,))
    p3 = multiprocessing.Process(target = selectMode, args = (sock,))
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()