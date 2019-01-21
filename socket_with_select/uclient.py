import socket
import sys
import select

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
inputs = [sock, sys.stdin]
outputs = [sock,]
writeCache = []

while True:
    readable, writeable, exeptions = select.select(inputs, outputs, [])
    for read in readable:
        if read == sys.stdin:
            sysin = sys.stdin.readline()
            writeCache.append(sysin.encode('utf-8'))
        elif read == sock:
            data, addr = sock.recvfrom(1024)
            print(f'receive frome server data {data}, addr {addr}')
            if not data or data == b'\n':
                inputs.remove(sock)
                outputs.remove(sock)
                exit()
        else:
            print(f'unkown readable {read}')
    for write in writeable:
        if write == sock:
            if writeCache:
                sock.sendto(writeCache.pop(), ('127.0.0.1',8001))
        else:
            print(f'unkown write {write}')
sock.close()