def random_string(length = 10):
    import random
    import string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))