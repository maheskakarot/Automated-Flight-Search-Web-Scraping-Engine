import os


def delete_file_from_os(file_name):
    os.remove('{}{}'.format('', file_name))
