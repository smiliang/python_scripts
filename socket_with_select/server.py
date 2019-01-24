# coding=utf-8
__author__ = 'chenglp'

"""socket,select, kqueue学习
"""

import socket
import select
import sys
import os
import traceback
import errno

HOST = '127.0.0.1'
PORT = 8001
BUFFER_SIZE = 1024

#生成socket，绑定ip端口
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
server.setblocking(False)
server.bind((HOST, PORT))

server.listen(5)

#创建输入监听列表
inputs = [server, sys.stdin]
outputs = [server]
writeCache = []

#select模式
def select_mode():
   print('select mode')
   running = True
   while running:
      try:
         #select轮询inputs列表获取可以读的描述符
         readable, writeable, exceptional = select.select(inputs, outputs, [])
      except select.error as e:
         break

      for each in readable:
         #如果是server，则accept创建链接，并将链接的描述符放入到inputs进行select监听
         if each == server:
            try:
               conn, addr = server.accept()
               inputs.append(conn)
               outputs.append(conn)
               print(f'incoming connect from {addr} accpet by {os.getpid()}')               
            except (OSError, IOError) as e:
               print(f'incoming connect,no gained. err:{e} by {os.getpid()}')            
         #如果是系统输入，则获取系统输入，停止程序
         elif each == sys.stdin:
            junk = sys.stdin.readline()
            running = False
            inputs.clear()
            outputs.clear()
            break
         #如果是其它的，则为socket链接，读取链接数据，并返回读取到的数据。
         else:
            try:
               data = each.recv(BUFFER_SIZE)
               print(f'receive from {each} data {data} pid {os.getpid()}')
               if data:
                  if data == b'\n':
                     inputs.remove(each)
                     outputs.remove(each)
                     each.close()
                     break
                  writeCache.append((data, each))
               else:
                  inputs.remove(each)
                  outputs.remove(each)
                  each.close()
            except socket.error as e:
               inputs.remove(each)
               outputs.remove(each)
      for write in writeable:
         for data,each in writeCache:
            if write == each:
               write.send(data)
               writeCache.remove((data,each))

   server.close()

#epoll模式
def epoll_mode():
   print('epoll mode')
   running = True
   epoll = select.epoll()

   #注册epoll读
   epoll.register(server.fileno(), select.EPOLLIN)
   #保存链接文件描述符和链接的对应关系
   conn_list = {}
   while running:
      try:
         #开始执行epoll
         events = epoll.poll(1)
      except:
         break
      if events:
         for fileno, event in events:
            #如果是新链接，则accept，并将新链接注册到epoll中
            if fileno == server.fileno():
               conn, addr = server.accept()
               conn.setblocking(0)
               epoll.register(conn.fileno(), select.EPOLLIN)
               conn_list[conn.fileno()] = conn
            #如果是其他的可读链接，则获取到链接，recv数据，如果是\n， 则close，并从epoll中unregister掉这个文件描述符
            elif event & select.EPOLLIN:
               data = conn_list[fileno].recv(BUFFER_SIZE)
               if not data or data.startswith(b'\n'):
                  conn_list[fileno].close()
                  epoll.unregister(fileno)
                  del(conn_list[fileno])
               else:
                  conn_list[fileno].send(data)

   server.close()

#kqueue模式
def kqueue_mode():
   print('kqueue mode')
   running = True
   kq = select.kqueue()
   conn_list = {}
   #生成kevents列表，监听socket的读操作
   kq.control([select.kevent(server.fileno(), select.KQ_FILTER_READ,select.KQ_EV_ADD), select.kevent(server.fileno(), select.KQ_FILTER_WRITE,select.KQ_EV_ADD)], 0)
   while running:
      try:
         #开始kqueue，如果有可执行kevent，则返回对应的kevent列表
         eventlist = kq.control(None,1024)
      except select.error as e:
         break
      if eventlist:
         for each in eventlist:
            #如果是socket链接，则accept，将conn创建kevent放入到events进行监听，将链接放入到conn_list进行保存，key为index。
            if each.ident == server.fileno():
               conn, addr = server.accept()
               conn_list[conn.fileno()] = conn
               kq.control([select.kevent(conn_list[conn.fileno()].fileno(), select.KQ_FILTER_READ, select.KQ_EV_ADD,udata=conn.fileno()),select.kevent(conn_list[conn.fileno()].fileno(), select.KQ_FILTER_WRITE, select.KQ_EV_ADD,udata=conn.fileno())], 0)
            else:
               try:
                  #如果不是socket链接，则获取到conn，然后进行读写操作。
                  if each.udata >= 1 and each.flags & select.KQ_EV_ADD and each.filter == select.KQ_FILTER_READ:
                     conn = conn_list[each.udata]
                     data = conn.recv(BUFFER_SIZE)
                     print(f'receive from {conn}, data {data}')
                     if not data or data.startswith(b'\n'):
                        kq.control([select.kevent(conn_list[each.udata].fileno(), select.KQ_FILTER_READ, select.KQ_EV_DELETE,udata=each.udata), select.kevent(conn_list[each.udata].fileno(), select.KQ_FILTER_WRITE, select.KQ_EV_DELETE,udata=each.udata)], 0)
                        del(conn_list[each.udata])
                        conn.close()
                     else:
                        writeCache.append((data, each.udata))
                  elif each.udata >= 1 and each.flags & select.KQ_EV_ADD and each.filter == select.KQ_FILTER_WRITE:
                     for data, udata in writeCache:
                        if udata == each.udata:
                           conn = conn_list[udata]
                           conn.send(data)
                           writeCache.remove((data,udata))
               except Exception as e:
                  print(e)      

   server.close()

#poll模式
def poll_mode():
   print('poll mode')
   running = True
   poll = select.poll()
   
   #注册poll读
   poll.register(server.fileno(), select.POLLIN | select.POLLOUT)
   #保存链接文件描述符和链接的对应关系
   conn_list = {}
   
   while running:
      try:
         events = poll.poll()
      except Exception as e:
         print(e)
      for fileno, event in events:
         if fileno == server.fileno():
            con, addr = server.accept()
            con.setblocking(False)
            poll.register(con.fileno(), select.POLLIN | select.POLLOUT)
            conn_list[con.fileno()] = con
         elif event & select.POLLIN:
            try:
               data = conn_list[fileno].recv(BUFFER_SIZE)
               print(f'receive from {conn_list[fileno]} data {data}')
               if not data or data.startswith(b'\n'):
                  conn_list[fileno].close()
                  poll.unregister(fileno)
                  del conn_list[fileno]
               else:
                  writeCache.append((data, fileno))
            except Exception as e:
               print(e)
         elif event & select.POLLOUT:
            for data, fno in writeCache:
               if fno == fileno:
                  conn_list[fileno].send(data)
                  writeCache.remove((data, fileno))
   server.close()
            
   

if __name__ == "__main__":
   #select_mode()
   #epoll_mode()
   #kqueue_mode()
   #poll_mode()
   childs = []
   isc = False
   for i in range(3):
      pid = os.fork()
      if 0 == pid:
         select_mode()
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