#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import random

list = []
a = random.randint(0,10000)
print(f'random {a}')
list.append(a)
print(f'list addr : {hex(id(list))}')
print(f'a addr ; {hex(id(a))}')

if True:
    child = []
    isc = False
    print(f'childs {child}')
    for i in range(3):
        print(f'**********%d*********** {i}')
        pid = os.fork()
        if pid == 0:
            # We are in the child process.
            print(f"{os.getpid()} (child) just was created by {os.getppid()}. i {i}")
            isc = True
            print(f'list addr : {hex(id(list))}')
            print(f'a addr ; {hex(id(a))}')            
            break
        else:
            # We are in the parent process.
            print(f"{os.getpid()} (parent) just created {pid}. i {i}")
            child.append(pid)
    if not isc:
        print(f"after childs {child}")
        print(f'servers {list}')
        print(f'list addr : {hex(id(list))}')
        print(f'a addr ; {hex(id(a))}')        
        for c in child:
            p,s = os.waitpid(c, 0)
            print(f'{p} status : {s}')