import os

def ensure_containing_directory(path):
    ensure_directory(os.path.dirname(path))

def ensure_directory(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
