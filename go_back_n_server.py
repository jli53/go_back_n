from socket import *
import struct
import random
serverPort = 7734
filename = 'gbn_file'
p = 0.98
serverSocket = socket(AF_INET,SOCK_DGRAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('',serverPort))
print 'ok'
(mss, clientAddr) = serverSocket.recvfrom(10)
print "" + mss
print clientAddr
MSS = int(mss)
global old_int_seq
old_int_seq = 0
global int_seq
int_seq = 0
global x
x= 0

def get_seq(message):
	global int_seq
	seq_string = message[0:4]
	int_seq = (struct.unpack('i',seq_string))[0]
	print 'get seq %d , size is %d' %(int_seq, len(message)-8)

def generate_ack(message):
	global int_seq
	message = message[8:]
	ack = int_seq + len(message)
	print 'going to send ack %d' %ack
	hex_ack = hex(ack)
	hex_ack = ('0'*(10-len(hex_ack)))+hex_ack[2:]
	reverse_hex_ack = hex_ack[6:8]+hex_ack[4:6]+hex_ack[2:4]+hex_ack[0:2]
	ack_message = reverse_hex_ack.decode("hex") + '\x00\x00\xAA\xAA'
	return ack_message

f = open(filename,'wb+')
(message, clientAddr)= serverSocket.recvfrom(MSS+8)
get_seq(message)
ack_message = generate_ack(message)
serverSocket.sendto(ack_message,clientAddr)
random_number = p
while True:
	if (int_seq - old_int_seq <= MSS) and ((int_seq > old_int_seq) or (int_seq ==0)) and random_number<=p:
		message = message[8:]
		f.write(message)
		old_int_seq = int_seq
		'''
		if len(message)< MSS:
			break;
		'''
	(message,clientAddr) = serverSocket.recvfrom(MSS+8)
	if message == 'OK':
		break;
	random_number = random.random()
	if random_number > p:
		x= x+1
	print '%f' %random_number
	get_seq(message)
	if random_number <= p:
		if (int_seq - old_int_seq <= MSS) and ((int_seq > old_int_seq) or (int_seq ==0)):
			ack_message = generate_ack(message)
			serverSocket.sendto(ack_message,clientAddr)
	else:
		print 'gonna drop seq %d' %int_seq
print 'finish receiving file '+filename
print 'x is %d' %x
f.close() 
