from gevent.monkey import patch_all
patch_all()

import time
import logging
import unittest

from gevent.pool import Group

from azrpc import AZRPCServer

from . import Lock, get_lock, is_locked, rpc


class Test(unittest.TestCase):
    def tassert(self, g, gw, result, value):
        assert g not in gw or result is value

    def _test_many_worker(self, g):
        result = is_locked('foo')
        self.tassert(g, 'ABC', result, False)
        print g, 1, result

        with get_lock('foo') as result:
            self.tassert(g, 'ABC', result, True)
            print g, 2, result

            result = is_locked('foo')
            self.tassert(g, 'ABC', result, True)
            print g, 3, result

            time.sleep(1)

        result = is_locked('foo')
        self.tassert(g, 'AB', result, True)
        self.tassert(g, 'C', result, False)
        print g, 4, result

    def test_many(self):
        group = Group()
        group.spawn(self._test_many_worker, 'A')
        group.spawn(self._test_many_worker, 'B')
        group.spawn(self._test_many_worker, 'C')
        group.join()

    def _test_long_worker(self, g):
        result = is_locked('foo')
        self.tassert(g, 'AB', result, False)
        print g, 1, result

        with get_lock('foo') as result:
            self.tassert(g, 'AB', result, True)
            print g, 2, result

            result = is_locked('foo')
            self.tassert(g, 'AB', result, True)
            print g, 3, result

            time.sleep(15)

        result = is_locked('foo')
        self.tassert(g, 'A', result, True)
        self.tassert(g, 'B', result, False)
        print g, 4, result

    def test_long(self):
        group = Group()
        group.spawn(self._test_long_worker, 'A')
        group.spawn(self._test_long_worker, 'B')
        group.join()

    def test_idle(self):
        lock = Lock('test_service')
        self.tassert('X', 'X', lock.is_locked(), False)
        with lock as result:
            self.tassert('X', 'X', result, True)
            self.tassert('X', 'X', lock.is_locked(), True)
            for _ in xrange(3):
                lock.idle()
                time.sleep(1)
        self.tassert('X', 'X', lock.is_locked(), False)


def main():
    logging.basicConfig(level=logging.INFO)
    AZRPCServer(rpc)
    unittest.main(failfast=True, catchbreak=True)

if __name__ == '__main__':
    main()
