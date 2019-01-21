import socket
import select
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
sock.bind(('127.0.0.1', 8001))

inputs = [sock, sys.stdin]
outputs = [sock,]
writeCache = []

#----------------------------------------------------------------------
def selectMode():
    print('select Mode')
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
            elif read == sock:
                data, addr = sock.recvfrom(1024)
                print(f'receive {data} from {addr}')
                writeCache.append(addr)
                writeCache.append(data)
            else:
                print(f'unkown read {read}')
        for write in writeable:
            if write == sock:
                if writeCache:
                    sock.sendto(writeCache.pop(), writeCache.pop())
            else:
                print(f'unkown write {write}')
    sock.close()
    
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
    selectMode()
    #pollMode()
    #kqueueMode()