from collections import defaultdict
from socket import gethostname
from sys import argv

def service_name():
    return argv[0].split("/")[-1]

def bykey(key, default, **kwargs):
    return defaultdict(lambda: default, **kwargs)[key]

def byhostname(default, **kwargs):
    return bykey(gethostname(), default, **kwargs)
