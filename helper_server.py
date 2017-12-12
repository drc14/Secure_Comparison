from random import randrange, choice, shuffle
from phe import paillier
from phe.util import invert

from helper_helper import send, receive, get_vector_input

get_vector_input_server = get_vector_input

def permute(l):
	other = [x for x in range(0, len(l))]
	shuffle(other)

	return [l[x] for x in other], other


def un_permute(l, other):
	a = [0] * len(l)

	for x, y in zip(l, other):
		a[y] = x

	return a


def secure_multiplication_server(client, public_key, u, v):
	# Pick two random numbers
	ra = randrange(0, public_key.n // 2)
	rb = randrange(0, public_key.n // 2)
	rarb = (ra * rb) % public_key.n

	a_prime = u + ra
	b_prime = v + rb


	# Send a' and b' to client
	send(client, a_prime)
	send(client, b_prime)

	# Recieve E(h) from client
	h_prime = receive(client)

	s = h_prime - (u * rb)
	s_prime = s - (v * ra)

	u_times_v = s_prime - rarb

	return u_times_v


def binary_decomposition_server(public_key, num):
	bd = [int(x) for x in "{0:b}".format(num)]
	bd = ([0] * (32 - len(bd))) + bd

	return [public_key.encrypt(x) for x in bd]

def secure_lsb_server(client, public_key, T, i):
	"""Based on Encrypted_LSB from Samanthula & Jiang."""
	r = public_key.get_random_lt_n()
	Y = T + r

	send(client, Y)

	alpha = receive(client)

	if not r % 2: # r is even
		return alpha
	else:
		return (1 - alpha)


def svr_server(client, public_key, enc_x, x_decomp):
	U = 0

	for i in range(0, len(x_decomp)):
		x_i = x_decomp[i] * (2**i)
		U += x_i

	V = U - enc_x
	W = V * public_key.get_random_lt_n()

	send(client, W)

	γ = receive(client)
	return γ


def secure_bit_decomposition_server(client, public_key, enc_x, bitlength_m):
	l_inv2 = paillier.EncodedNumber.encode(public_key, invert(2, public_key.n))
	T = enc_x + 0
	x_decomp = []

	send(client, bitlength_m)

	for i in range(0, bitlength_m):
		x_decomp.append(secure_lsb_server(client, public_key, T, i))
		Z = T - x_decomp[i]
		T = Z * l_inv2

	if svr_server(client, public_key, enc_x, x_decomp) == 1:
		return list(reversed(x_decomp))
	else:
		return secure_bit_decomposition_server(client, public_key, enc_x, bitlength_m)

def secure_bitor_server(client, public_key, o1, o2):
	# Since o1 & o2 are bits, o1 * o2 = o1 AND o2
	o1_AND_o2 = secure_multiplication_server(client, public_key, o1, o2)

	# E(o1 OR o2) = E(o1+o2) * E(o1 AND o2)^(N-1)
	o1_OR_o2 = (o1+o2) - o1_AND_o2

	return o1_OR_o2

def secure_minimum_server(client, public_key, u_decomp, v_decomp):
	# Randomly choose functionality F
	F = choice(['u > v', 'u < v'])

	# Initalize
	H_i = public_key.encrypt(0)
	L = []
	Gamma = []
	r = []

	# For each bit
	for u_i, v_i in zip(u_decomp, v_decomp):
		u_times_v = secure_multiplication_server(client, public_key, u_i, v_i)

		# Append random number r^
		r.append(public_key.get_random_lt_n())
		if F == 'u > v':
			W_i = u_i - u_times_v
			Gamma.append((v_i - u_i) + public_key.encrypt(r[-1]))
		else:
			W_i = v_i -u_times_v
			Gamma.append((u_i - v_i) + public_key.encrypt(r[-1]))

		# XOR
		G_i = u_i + v_i + - 2 * u_times_v

		H_i = (H_i * public_key.get_random_lt_n()) + G_i

		Phi_i = H_i - 1

		L.append(W_i + (Phi_i * public_key.get_random_lt_n()))

	Gamma_prime, gamma_permute_key = permute(Gamma)
	L_prime, _ = permute(L)

	send(client, Gamma_prime)
	send(client, L_prime)

	# Recieve M' and E(alpha)
	M_prime = receive(client)
	alpha = receive(client)

	# De-permute M
	M = un_permute(M_prime, gamma_permute_key)

	minimum = []
	for i in range(32):
		lambda_i = M[i] + (alpha * (public_key.n - r[i]))

		if F == 'u > v':
			minimum.append(u_decomp[i] + lambda_i)
		else:
			minimum.append(v_decomp[i] + lambda_i)

	total_minimum = public_key.encrypt(0)
	for i in range(len(minimum)):
		total_minimum += (minimum[31-i] * (2 ** i))

	return total_minimum


def secure_squared_euclidean_distance_server(client, public_key, u, v):
	u_minus_v = [(a - b) for a, b in zip(u, v)]

	squared = [secure_multiplication_server(client, public_key, x, x) for x in u_minus_v]

	summed = public_key.encrypt(0)

	for i in squared:
		summed += i

	return summed
