from socket import *
import thread
from threading import *
from time import *
import struct
serverName = '152.46.20.100'
serverPort = 7734
serverAddr = (serverName,serverPort)
filename = 'gbn_file'
time = 0.2
global seq
global N
global window
global timeout
global more_seq
more_seq = 1
timeout = 0
seq = 0
N = 55
window = []
MSS = 2048
global lock
lock = Lock()
global t

'''set timer handler'''
def gbn_timeout():
	print 'timeout'
	global timeout
	lock.acquire()
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
	global more_seq
	old_int_ack = 0
	next = 1
	while True:
		ack = ''
		(ack,serverAddr) = clientSocket.recvfrom(8)
		ack_string = ack[0:4]
		int_ack = (struct.unpack('i',ack_string))[0]
		print 'get ack for %d' %int_ack
		t.cancel()
		del t
		t = Timer(time,gbn_timeout)
		t.start()
		lock.acquire()
		N = N+1
		del window[0]
		lock.release()
		print 'now n = '+str(N)
		if more_seq == 0:
			if int_ack == seq:
				t.cancel()
				del t
				break

clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.sendto(str(MSS),serverAddr)
receive_thread = Thread(target = receive_ack, args= (MSS,))
receive_thread.start()
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
		data = reverse_hex_seq.decode("hex")+'\x00\x00\x55\x55'+data
		while N == 0:
			if timeout == 1:
				go_back_size = 0
				lock.acquire()
				N = N + len(window)
				N = N-1
				while len(window) > 1:
					go_back_size = go_back_size-len(window[-1])+8
					del window[-1]
				seq = seq + go_back_size
				print '1.resend seq before %d' %seq
				lock.release()
				f.seek(go_back_size-len(data)+8,1)
				clientSocket.sendto(window[0],serverAddr)
				t = Timer(time,gbn_timeout)
				t.start()		
				data = f.read(MSS)
				'''
				print 'just read file, position %d' %(f.tell())
				'''
		if timeout == 1:
			timeout = 0
			continue
		print 'send seq %d' %seq
		lock.acquire()
		window.append(data)
		N = N-1
		seq = seq + len(data)-8
		lock.release()
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
		print '2.resend seq before %d' %seq
		lock.release()
		f.seek(go_back_size,1)
		clientSocket.sendto(window[0],serverAddr)
		timeout = 0
		t = Timer(time,gbn_timeout)
		t.start()		
	data = f.read(MSS)
	if not data:
		more_seq = 0
clientSocket.sendto('OK',serverAddr)
clientSocket.close()
print 'finish sending file '+filename