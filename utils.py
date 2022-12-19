import os

def check_and_make_dir(path_dir):
    if not os.path.exists(os.path.dirname(path_dir)):
        # print("make new dir.")
        os.makedirs(os.path.dirname(path_dir))
