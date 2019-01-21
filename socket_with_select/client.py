# coding=utf-8
import socket
import select
import sys


HOST = '127.0.0.1'
PORT = 8001
BUFFER_SIZE = 1024


# 创建socket链接，链接服务器
s = socket.socket()
s.setblocking(False)
try:
   s.connect((HOST, PORT))
except socket.error as e:
   print(e)

#创建读写监听列表
readlist = [s, sys.stdin]
writelist = [s, ]
#输入缓存
writeCache = []

while True:
   try:
      #select监听获取可读可写
      readable, writeabel, exceptional = select.select(readlist, writelist, [])
   except select.error as e:
      break

   for each in readable:
      #如果是系统输入，则获取输入信息放到输入缓存里
      if each == sys.stdin:
         inputs = sys.stdin.readline()
         writeCache.append(inputs.encode('utf-8'))
      #如果是socket，则接受数据
      elif each == s:
         data = s.recv(BUFFER_SIZE)
         print(f'receive from {s} data {data}')
         if not data:
            readlist.remove(s)
            writelist.remove(s)
            s.close()
            exit()
      else:
         pass
   for each in writeabel:
      #如果是socket并且写缓存有数据，则发送数据
      if each == s and writeCache:
         s.sendall(writeCache.pop())
s.close()
