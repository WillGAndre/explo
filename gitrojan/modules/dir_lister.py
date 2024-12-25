import os


def run(**kwargs):
    print('\t [+] Loading directory lister module')
    files = os.listdir('.')
    return str(files)