import secrets
from math import gcd

def lcm(a, b):
    return abs(a * b) // gcd(a, b)

def modular_inverse(a, m):
    g, x, y = extended_gcd(a, m)
    if g != 1:
        raise Exception('Modular inverse does not exist')
    return x % m

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    return g, y1 - (b // a) * x1, x1

def generate_paillier_keys():
    p = 494590142757270273291563853101704253171
    q = 525852504996386417770519176313761623963
    n = p * q
    n_sq = n * n
    lambda_key = lcm(p - 1, q - 1)
    g = n + 1 
    mu = modular_inverse(lambda_key, n)
    return (n, g), (lambda_key, mu)

def paillier_encrypt(public_key, plaintext):
    n, g = public_key
    n_sq = n * n
    r = secrets.randbelow(n - 1) + 1
    while gcd(r, n) != 1:
        r = secrets.randbelow(n - 1) + 1
    c = (pow(g, plaintext, n_sq) * pow(r, n, n_sq)) % n_sq
    return c

def paillier_decrypt(public_key, private_key, ciphertext):
    n, g = public_key
    lambda_key, mu = private_key
    n_sq = n * n
    u = pow(ciphertext, lambda_key, n_sq)
    l_x = (u - 1) // n
    return (l_x * mu) % n

def split_secret_key(secret_integer, threshold=2, total_shares=3):
    FIELD = 2**521 - 1
    coefficients = [secret_integer] + [secrets.randbelow(FIELD) for _ in range(threshold - 1)]
    shares = []
    for x in range(1, total_shares + 1):
        y = sum(c * pow(x, i, FIELD) for i, c in enumerate(coefficients)) % FIELD
        shares.append((x, y))
    return shares

def reconstruct_secret_key(shares):
    FIELD = 2**521 - 1
    secret = 0
    for i, (x_i, y_i) in enumerate(shares):
        num = 1
        den = 1
        for j, (x_j, _) in enumerate(shares):
            if i != j:
                num = (num * (-x_j)) % FIELD
                den = (den * (x_i - x_j)) % FIELD
        lagrange = (num * modular_inverse(den, FIELD)) % FIELD
        secret = (secret + y_i * lagrange) % FIELD
    return secret