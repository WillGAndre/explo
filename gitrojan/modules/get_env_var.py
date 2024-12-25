import os


def run(**kwargs):
    print('\t [+] Loading environment variables')
    return str(os.environ)