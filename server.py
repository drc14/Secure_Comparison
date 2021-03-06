#!/usr/bin/env python3
import socket
import argparse

from helper_helper import send, receive, get_vector_input, DEFAULT_PORT
from helper_server import secure_kNN_Bob, recompose, handle_sknn_output, \
	secure_multiplication_server, secure_bit_decomposition_server, \
	secure_minimum_server, secure_minimum_of_n_server, \
	secure_bitor_server, secure_squared_euclidean_distance_server


parser = argparse.ArgumentParser(description="Server for SkNN and its "
								"subprotocols.")
parser.add_argument('port', type=int, default=DEFAULT_PORT, nargs='?',
					help='port to listen on (default: %(default)s)')
parser.add_argument('--host', default='localhost', dest='host',
					help='hostname to listen on (default: %(default)s)')

ARGS = parser.parse_args()
port = ARGS.port
host = ARGS.host

# create a socket object
serversocket = socket.socket(
	        socket.AF_INET, socket.SOCK_STREAM)

# Try to make it so socket closes quickly
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind to the port
serversocket.bind((host, port))

# queue up to 10 requests
serversocket.listen(10)

# establish a connection
print("Waiting for a client connection on {}...".format(port))
client, addr = serversocket.accept()

print("Got a connection!")

### Recieve Config Parameters ###
# Key
public_key = receive(client)
print("Got public key")
##########################

while True:
	# Recieve menu option
	option = receive(client)

	if option in ('c1', 'c2'):
		# job is 'bob'
		if option == 'c1':
			client.close()
			raise RuntimeError("C2 must be started before C1.")

		C2 = client
		port_C1C2 = receive(C2)
		assert isinstance(port_C1C2, int)

		print("Secure k-Nearest Neighbor selected by C2, you are Bob.")

		port_C1 = port + 1
		socket_C1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		socket_C1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		socket_C1.bind((host, port_C1))
		socket_C1.listen(10)
		print("Start C1 with options '{} -o c1'; I'll wait".format(port_C1))
		C1, addr = socket_C1.accept()
		print("Heard from C1!")

		pk_C1 = receive(C1)
		assert pk_C1 is None
		option_C1 = receive(C1)
		if option_C1 != 'c1':
			raise RuntimeError("C1 MUST select C1; got {!r}".format(option_C1))

		send(C1, port_C1C2)

		print("Please enter the query tuple Q: ", end='')
		Q = tuple(map(int, input().split()))

		print("Please enter k, the number of records: ", end='')
		k = int(input())

		send(C1, k)
		send(C2, k)

		m_n = receive(C1)
		assert isinstance(m_n, tuple) and len(m_n) == 2
		m, n = m_n

		if len(Q) != m:
			raise RuntimeError("Length of Q doesn't match length of "
				"database records; {} vs {}".format(len(Q), m))

		print("Starting SkNN.")
		t_prime = secure_kNN_Bob(C1, C2, public_key, Q, k, m, n)

		print("Finished SkNN.")
		handle_sknn_output(t_prime)

	elif option == '1':
		print("Secure multiplication selected, please enter u: ", end='')
		# Get u from user
		u = public_key.encrypt(int(input()))
		# Recieve v from client
		v = receive(client)
		print("received V")
		u_times_v = secure_multiplication_server(client, public_key, u, v)

		# For Confirmation
		print("Finished secure multiplication, sending to client for your confirmation...")
		send(client, u_times_v)

	elif option == '2':
		print("Secure minimum selected, please enter u: ", end='')
		enc_u = public_key.encrypt(int(input()))
		enc_v = receive(client)
		u_decomp = secure_bit_decomposition_server(client, public_key, enc_u, 32)
		v_decomp = secure_bit_decomposition_server(client, public_key, enc_v, 32)
		minimum = secure_minimum_server(client, public_key, u_decomp, v_decomp)
		min_recomp = recompose(public_key, minimum)
		print("Finished secure minimum, sending to client for your confirmation...")
		send(client, min_recomp)

	elif option == '3':
		print("Secure squared euclidean distance selected, please enter u: ", end='')
		u = get_vector_input(public_key)
		v = receive(client)
		ssed = secure_squared_euclidean_distance_server(client, public_key, u, v)
		print("Finished secure squared euclidean distance, sending to client for your confirmation...")
		send(client, ssed)

	elif option == '4':
		print("Secure bit decomposition selected.")
		enc_x = receive(client)
		m = receive(client)
		print("Received E(x) and m; running secure bit decomposition.")
		x_decomp = secure_bit_decomposition_server(client, public_key, enc_x, m)
		print("Finished secure bit decomposition, sending to client")
		send(client, x_decomp)

	elif option == '5':
		print("Secure Bit-OR selected, please enter o1 [0,1]: ", end='')
		o1 = public_key.encrypt(bool(int(input())))
		o2 = receive(client)
		bitor = secure_bitor_server(client, public_key, o1, o2)
		print("Finished secure Bit-OR, sending to client for your confirmation...")
		send(client, bitor)

	elif option == '6':
		print("Secure minimum-of-n selected.")
		enc_d = receive(client)
		d_min = secure_minimum_of_n_server(client, public_key, enc_d)
		d_min_recomp = recompose(public_key, d_min)
		print("Finished secure minimum-of-n, sending to client...")
		send(client, d_min_recomp)

	elif option == '9':
		break

	else:
		print("Unexpected value from client: {!r}".format(option))

print("Closing connection")
client.close()
serversocket.close()


"""
   msg = 'Thank you for connecting'+ "\r\n"

   public_key = pickle.loads(clientsocket.recv(4096))
   clientsocket.send(pickle.dumps(public_key.encrypt(10)))

#clientsocket.send(msg.encode('ascii'))
clientsocket.close()
"""
