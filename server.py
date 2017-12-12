import socket
from phe import paillier
from helper_server import *
import pickle
from sys import getsizeof, argv

if len(argv) != 2:
	print("Usage: python3 {} (port number)".format(argv[0]))
	quit()

# create a socket object
serversocket = socket.socket(
	        socket.AF_INET, socket.SOCK_STREAM)

# get local machine name
host = 'localhost'


# Try to make it so socket closes quickly
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
port = int(argv[1])

# bind to the port
serversocket.bind((host, port))

# queue up to 10 requests
serversocket.listen(10)

# establish a connection
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

	if '1' in option:
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
	elif '2' in option:
		print("Secure minimum selected, please enter u: ", end='')
		enc_u = public_key.encrypt(int(input()))
		enc_v = receive(client)
		u_decomp = secure_bit_decomposition_server(client, public_key, enc_u, 32)
		v_decomp = secure_bit_decomposition_server(client, public_key, enc_v, 32)
		minimum = secure_minimum_server(client, public_key, u_decomp, v_decomp)
		print("Finished secure minimum, sending to client for your confirmation...")
		send(client, minimum)
	elif '3' in option:
		print("Secure squared euclidean distance selected, please enter u: ", end='')
		u = get_vector_input_server(public_key)
		v = receive(client)
		ssed = secure_squared_euclidean_distance_server(client, public_key, u, v)
		print("Finished secure squared euclidean distance, sending to client for your confirmation...")
		send(client, ssed)

	elif '4' in option:
		print("Secure bit decomposition selected.")
		enc_x = receive(client)
		m = receive(client)
		print("Received E(x) and m; running secure bit decomposition.")
		x_decomp = secure_bit_decomposition_server(client, public_key, enc_x, m)
		print("Finished secure bit decomposition, sending to client")
		send(client, x_decomp)

	elif '5' in option:
		print("Secure Bit-OR selected, please enter o1 [0,1]: ", end='')
		o1 = public_key.encrypt(bool(int(input())))
		o2 = receive(client)
		bitor = secure_bitor_server(client, public_key, o1, o2)
		print("Finished secure Bit-OR, sending to client for your confirmation...")
		send(client, bitor)

	elif '9' in option:
		break

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
