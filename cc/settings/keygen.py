# Autogenerate secret keys.

import random

KEY_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

KEY_FILE_TEMPLATE = """# Auto-generated secret key.
SECRET_KEY = '%(key)s'
"""

def generate_secret_key(path):
    key = ''.join([random.choice(KEY_CHARS) for i in range(50)])
    content = KEY_FILE_TEMPLATE % locals()
    with open(path, 'w') as f:
        f.write(content)

