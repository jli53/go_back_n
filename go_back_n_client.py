from socket import *
from math import ceil
import os
import thread
from threading import *
from time import *
import struct
import timeit
import sys
start = timeit.default_timer()
serverName = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddr = (serverName,serverPort)
filename = sys.argv[3]
time = 0.2
global seq
global int_ack
global N
global size
global window
global timeout
global more_seq
global old_int_ack
int_ack = 0
old_int_ack =0
more_seq = 1
timeout = 0
seq = 0
N = int(sys.argv[4])
window = []
MSS = int(sys.argv[5])
global lock
lock = Lock()
global t

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

'''set timer handler'''
def gbn_timeout():
	global old_int_ack
	global timeout
	lock.acquire()
	print 'Timeout, sequence number is %d' %(old_int_ack)
	timeout = 1
	lock.release()

t = Timer(time, gbn_timeout)

'''set a new thread to receive ack'''
def receive_ack(mss):
	global seq
	global N
	global window
	global lock
	global t
	global size
	global more_seq
	global old_int_ack
	global int_ack
	next = 1
	while True:
		ack = ''
		(ack,serverAddr) = clientSocket.recvfrom(8)
		ack_string = ack[0:4]
		lock.acquire()
		int_ack = (struct.unpack('i',ack_string))[0]
		if (int_ack > old_int_ack):
			'''
			print 'get ack for %d' %int_ack
			'''
			t.cancel()
			del t
			if int_ack == size:
				lock.release()
				break;
			t = Timer(time,gbn_timeout)
			t.start()
			number_ack = ceil(float(int_ack-old_int_ack)/float(MSS))
			if number_ack > 1:
				print 'earlier ack have not come back'
			N = N + number_ack
			'''
			problem is here
			should add [(int_ack-old_int_ack)/MSS]
			and del more window below:
			'''
			while number_ack:
				if len(window)>0:
					del window[0]
				number_ack = number_ack - 1
			'''
			print 'now n = '+str(N)
			'''
			old_int_ack = int_ack
			lock.release()
		else:
			lock.release()
			'''
			print 'earlier ack just come back'
			'''

clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.sendto(str(MSS),serverAddr)
receive_thread = Thread(target = receive_ack, args= (MSS,))
receive_thread.start()
f1= open(filename,'r')
f1.seek(0, os.SEEK_END)
size = f1.tell()
f1.close()
f = open(filename,'rb+')
data = f.read(MSS)
'''
print 'just read file, position %d' %(f.tell())
'''
t.start()
while data or receive_thread.isAlive():
	if data:
		'''
		print 'read data from file, size is %d' %len(data)
		'''
		hex_seq = hex(seq)
		hex_seq = ('0'*(10-len(hex_seq)))+hex_seq[2:]
		reverse_hex_seq = hex_seq[6:8]+hex_seq[4:6]+hex_seq[2:4]+hex_seq[0:2]
		check = checksum(data)
		'''
		print 'real chekc is %d' %check
		'''
		hex_check = hex(check)
		hex_check = ('0'*(6-len(hex_check)))+hex_check[2:]
		reverse_hex_check = hex_check[2:4]+hex_check[0:2]
		data = reverse_hex_seq.decode("hex")+reverse_hex_check.decode("hex")+'\x55\x55'+data
		lost = 0
		while N == 0:
			if timeout == 1:
				go_back_size = 0
				lock.acquire()
				N = N + len(window)
				'''
				print 'len of window is %d' %(len(window))
				'''
				N = N-1
				'''
				print 'after send, N is %d' %N
				'''
				while len(window) > 1:
					go_back_size = go_back_size-len(window[-1])+8
					del window[-1]
				seq = seq + go_back_size
				'''
				print '1.resend seq before %d' %seq
				'''
				if len(data) == MSS:
					f.seek(go_back_size-len(data),1)
				else:
					f.seek(go_back_size-len(data)+8,1)
				clientSocket.sendto(window[0],serverAddr)
				t.cancel()
				'''
				del t
				'''
				t = Timer(time,gbn_timeout)
				t.start()
				timeout = 0
				lost = 1
				lock.release()
				data = f.read(MSS)
				if not data:
					more_seq = 0
				'''
				print 'just read file, position %d' %(f.tell())
				'''
		if lost == 1:
			continue
		'''
		print 'send seq %d' %seq
		'''
		lock.acquire()
		window.append(data)
		N = N-1
		seq = seq + len(data)-8
		lock.release()
		if len(data) == 8:
			print 'empty packet 111111111111111111111111111111111111'
		clientSocket.sendto(data,serverAddr)
	if timeout == 1:
		go_back_size = 0
		lock.acquire()
		N = N + len(window)
		N = N-1
		while len(window) > 1:
			go_back_size = go_back_size-len(window[-1])+8
			del window[-1]
		seq = seq + go_back_size
		'''
		print '2.resend seq before %d' %seq
		'''
		lock.release()
		f.seek(go_back_size,1)
		if len(window[0]) == 8:
			print 'empty packet 222222222222222222222222222222'
		clientSocket.sendto(window[0],serverAddr)
		lock.acquire()
		timeout = 0
		t.cancel()
		'''
		del t
		'''
		t = Timer(time,gbn_timeout)
		t.start()		
		lock.release()
	data = f.read(MSS)
clientSocket.sendto('OK',serverAddr)
clientSocket.close()
print 'finish sending file '+filename
stop = timeit.default_timer()
print stop - start
