#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import random
from multiprocessing import Pipe, Queue
import sys
import select

list = []
a = random.randint(0,10000)
print(f'random {a}')
list.append(a)
#print(f'list origin addr : {hex(id(list))}')
#print(f'a addr : {hex(id(a))}')

if True:
    child = []
    isc = False
    print(f'childs {child}')
    
    #parent_conn, child_conn = Pipe()
    queue = Queue()
    
    for i in range(3):
        print(f'**********%d*********** {i}')
        pid = os.fork()
        if pid == 0:
            # We are in the child process.
            print(f"{os.getpid()} (child) just was created by {os.getppid()}. i {i}")
            isc = True
            #print(f'list child addr : {hex(id(list))}')
            #print(f'a addr : {hex(id(a))}')
            #a += 5
            #print(f'a modified addr : {hex(id(a))}')
            receiveCache = []
            while True:
                #readable, writeable, exceptions = select.select([child_conn], [child_conn], [])
                readable, writeable, exceptions = select.select([queue._reader], [queue._writer], [])                
                for read in readable:
                    try:
                        #data = child_conn.recv()
                        data = queue.get()
                        print(f'receive {data} pid {os.getpid()}')
                        receiveCache.append(data + b' '+ str(os.getpid()).encode('utf-8'))                        
                    except Exception as e:
                        print(f'exception {e}, pid {os.getpid()}')
                for write in writeable:
                    if receiveCache:
                        #child_conn.send(receiveCache.pop())
                        queue.put(receiveCache.pop())
                        pass
                    break
                else:
                    print(f'can\'t write pid {os.getpid()}')
            break
        else:
            # We are in the parent process.
            print(f"{os.getpid()} (parent) just created {pid}. i {i}")
            child.append(pid)
    if not isc:
        print(f"before childs {child}")
        #print(f'servers {list}')
        #print(f'list father addr : {hex(id(list))}')
        #print(f'a addr : {hex(id(a))}')
        #print(f'a value : {a}')
        sendCache = []
        while True:
            #readable, writeable, exceptions = select.select([sys.stdin, parent_conn], [parent_conn], [])
            readable, writeable, exceptions = select.select([sys.stdin, queue._reader], [queue._writer], [])
            for read in readable:
                if read == sys.stdin:
                    data = sys.stdin.readline().encode('utf-8')
                    sendCache.append(data)
                #elif read == parent_conn:
                #   data = parent_conn.recv()
                #   print(f'receive back {data}')
                elif read == queue._reader:
                    data = queue.get()
                    print(f'receive back {data}')
            for write in writeable:
                if sendCache:
                    #parent_conn.send(sendCache.pop())
                    queue.put(sendCache.pop())
                    
        for c in child:
            p,s = os.waitpid(c, 0)
            print(f'{p} status : {s}')
        #print(f'list after father addr : {hex(id(list))}')            
        #print(f'a addr : {hex(id(a))}')
        #print(f'a value : {a}')