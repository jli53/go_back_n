from socket import *
import struct
import random
serverPort = 7734
filename = 'a'
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
	'''
	print 'get seq %d' %(int_seq)
	'''

def generate_ack(message):
	global int_seq
	message = message[8:]
	ack = int_seq + len(message)
	'''
	print 'going to send ack %d' %ack
	'''
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
	get_seq(message)
	if (int_seq - old_int_seq <= MSS):
		if ((int_seq >old_int_seq) or (int_seq ==0)):
			random_number = random.random()
			'''
			print '%f' %random_number
			'''
			if random_number <= p:
				ack_message = generate_ack(message)
				serverSocket.sendto(ack_message,clientAddr)
			else:
				x= x+1
				print 'Packet lost, sequence numebr is %d' %int_seq
		elif int_seq <= old_int_seq:
			ack_message = generate_ack(message)
			serverSocket.sendto(ack_message,clientAddr)
print 'finish receiving file '+filename
print 'x is %d' %x
f.close() 
