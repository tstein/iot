from collections import defaultdict
from socket import gethostname

def bykey(key, default, **kwargs):
    return defaultdict(lambda: default, **kwargs)[key]

def byhostname(default, **kwargs):
    return bykey(gethostname(), default, **kwargs)
