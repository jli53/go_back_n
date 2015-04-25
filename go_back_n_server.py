from socket import *
import sys
import struct
import random
serverPort = int(sys.argv[1])
filename = sys.argv[2]
p = float(sys.argv[3])
p = 1 - p
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
real_check = 0
exp_check = 0

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def get_seq(message):
	global int_seq
	seq_string = message[0:4]
	int_seq = (struct.unpack('i',seq_string))[0]
	'''
	print 'get seq %d' %(int_seq)
	'''

def get_check(message):
	check_string = message[4:6]
	int_check = (struct.unpack('h',check_string))[0]
	if int_check < 0:
		int_check = 65536 + int_check
	return int_check

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
	exp_check = get_check(message)
	real_check = checksum(message[8:])
	if (int_seq - old_int_seq <= MSS):
		if ((int_seq >old_int_seq) or (int_seq ==0)):
			random_number = random.random()
			'''
			print '%f' %random_number
			'''
			if exp_check == real_check:
				'''
				print 'checksum righttttttttttttttt'
				'''
				if random_number <= p:
					ack_message = generate_ack(message)
					serverSocket.sendto(ack_message,clientAddr)
				else:
					x= x+1
					print 'Packet lost, sequence number = %d' %int_seq
			else:
				print 'exp_check is %d' %exp_check
				print 'real_check is %d' %real_check
				print 'checksum wrong!!!!!!!!!!'
		elif int_seq <= old_int_seq:
			ack_message = generate_ack(message)
			serverSocket.sendto(ack_message,clientAddr)
print 'finish receiving file '+filename
print 'x is %d' %x
f.close() 
