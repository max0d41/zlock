import os
import time
import logging

from gevent.lock import Semaphore
from contextlib import contextmanager
from weakref import WeakValueDictionary

from azrpc import AZRPC

logger = logging.getLogger(__name__)


class ZLockRPC(AZRPC):
    def get_client_address(self, target):
        if target is None:
            target = 'localhost'
        return target


LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 47001))
DEFAULT_TARGET = os.environ.get('ZLOCK_MASTER', None)
HEARTBEAT_TIMEOUT = int(os.environ.get('HEARTBEAT_TIMEOUT', 10))

rpc = ZLockRPC('zlock', LISTEN_PORT, heartbeat_timeout=HEARTBEAT_TIMEOUT)


# Server code

_global_lock = Semaphore()
_locks = WeakValueDictionary()

class MySemaphore(object):
    def __init__(self):
        self.sema = Semaphore()

@rpc.register
def _get_lock(name, try_=False):
    with _global_lock:
        if name not in _locks:
            if try_:
                yield False
                return
            lock = MySemaphore()
            _locks[name] = lock
        else:
            lock = _locks[name]
            if try_ and lock.locked():
                yield False
                return
    with lock.sema:
        logger.info('%s: Acquired')
        yield True
        try:
            # Wait forever, the client will send a CLI_CANCEL message or will be
            # timed out
            while True:
                time.sleep(60)
        finally:
            logger.info('%s: Released')

@rpc.register('zlock.is_locked')
def _is_locked(name):
    with _global_lock:
        if name not in _locks:
            return False
        lock = _locks[name]
    return lock.sema.locked()


# Client code

@contextmanager
def get_lock(name, try_=False, target=DEFAULT_TARGET):
    """Acquires or tries to acquire the lock. Returns `True` when the lock is
    acquired.
    """
    gen = _get_lock.stream(target, name, try_)
    got_lock = next(gen)
    yield got_lock
    if got_lock:
        # Just make a backend call to let the lock release
        _is_locked.execute(target, name)

def is_locked(name, target=DEFAULT_TARGET):
    return _is_locked.execute(target, name)
