from datetime import datetime, timedelta
import jwt

PRIVATE_KEY = '''
'''


def encode_token(payload, private_key):
    return jwt.encode(payload, private_key, algorithm='RS256')


def generate_token_header(username, private_key):
    '''
    Generate a token header base on the username.
    Sign using the private key.
    '''
    payload = {
        'username': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'role': 'ADMIN'
    }
    token = encode_token(payload, private_key).decode('utf-8')
    return f'Bearer {token}'


# Generate Bearer Token for Root User (Initial Setup)
bearer_token = generate_token_header('root', PRIVATE_KEY)
print(bearer_token)
