from gevent.monkey import patch_all
patch_all()

import time
import logging

from uuid import uuid4
from gevent.pool import Group

from . import get_lock, is_locked

uuid = uuid4().get_hex()

"""print uuid, 1
with get_lock('foo'):
    print uuid, 2, is_locked('foo')
    print uuid, 2, is_locked.execute(None, 'foo')
print uuid, 3
"""

def tassert(g, gw, result, value):
    assert g not in gw or result is value

def worker(g):
    result = is_locked('foo')
    tassert(g, 'ABC', result, False)
    print g, 1, result

    with get_lock('foo') as result:
        tassert(g, 'ABC', result, True)
        print g, 2, result

        result = is_locked('foo')
        tassert(g, 'ABC', result, True)
        print g, 3, result

        time.sleep(1)

    result = is_locked('foo')
    tassert(g, 'AB', result, True)
    tassert(g, 'C', result, False)
    print g, 4, result

def test():
    logging.basicConfig(level=logging.INFO)
    group = Group()
    group.spawn(worker, 'A')
    group.spawn(worker, 'B')
    group.spawn(worker, 'C')
    group.join()

if __name__ == '__main__':
    test()
