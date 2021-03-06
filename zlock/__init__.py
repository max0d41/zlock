import os
import logging

from gevent import GreenletExit, Timeout
from gevent.lock import Semaphore
from contextlib import contextmanager
from weakref import WeakValueDictionary, WeakSet

from azrpc import AZRPC, AZRPCTimeout

logger = logging.getLogger(__name__)


DEFAULT_TARGET = os.environ.get('ZLOCK_MASTER', None)
ZLOCK_LISTEN_PORT = int(os.environ.get('ZLOCK_LISTEN_PORT', 47001))
HEARTBEAT_TIMEOUT = int(os.environ.get('HEARTBEAT_TIMEOUT', 10))

rpc = AZRPC('zlock', ZLOCK_LISTEN_PORT, heartbeat_timeout=HEARTBEAT_TIMEOUT)


# Server code

global_lock = Semaphore()
locks = WeakValueDictionary()
waiting = WeakSet()


class MySemaphore(object):
    def __init__(self):
        self.sema = Semaphore()


class Waiter(object):
    pass


stats = {
    'requests': 0,
    'already_locked': 0,
    'try_failed': 0,
    'acquired': 0,
    'released': 0,
    'timeout': 0,
    'unexpected': 0,
    'failed': 0,
    'failed_timeout': 0,
    'exceptions': 0,
}


@rpc.register
def _get_lock(name, try_=False):
    stats['requests'] += 1
    with global_lock:
        if name not in locks:
            lock = MySemaphore()
            locks[name] = lock
        else:
            lock = locks[name]
    if lock.sema.locked():
        stats['already_locked'] += 1
        if try_:
            stats['try_failed'] += 1
            yield False
            return
    logger.debug('%s: Trying to acquire', name)
    try:
        waiter = Waiter()
        waiting.add(waiter)
        with lock.sema:
            del waiter
            stats['acquired'] += 1
            logger.debug('%s: Acquired', name)
            try:
                while True:
                    yield True
            except (GeneratorExit, GreenletExit):
                stats['released'] += 1
                logger.debug('%s: Released', name)
            except AZRPCTimeout:
                stats['timeout'] += 1
                logger.info('%s: Timed out', name)
            else:
                stats['unexpected'] += 1
                logger.warning('%s: Released without error', name)
    except (GeneratorExit, GreenletExit):
        stats['failed'] += 1
        logger.warning('%s: Released before getting lock', name)
    except AZRPCTimeout:
        stats['failed_timeout'] += 1
        logger.warning('%s: Timed out before getting lock', name)
    except:
        stats['exception'] += 1
        logger.exception('Exception at lock %s', name)
        raise


@rpc.register('zlock.is_locked')
def _is_locked(name):
    with global_lock:
        if name not in locks:
            return False
        lock = locks[name]
    return lock.sema.locked()


# Client code

class Lock(object):
    gen = None
    got = False

    def __init__(self, name, try_=False, target=DEFAULT_TARGET):
        self.name = name
        self.try_ = try_
        self.target = target

    def acquire(self):
        self.gen = _get_lock.stream_sync(self.target, self.name, self.try_)
        self.got = next(self.gen)
        return self.got

    def release(self):
        assert self.got
        if self.got:
            #_is_locked.execute(self.target, self.name)
            self.got = False
            del self.gen
            try:
                with Timeout(1):
                    self.locked()
            except Exception:
                pass

    def locked(self):
        return _is_locked.execute(self.target, self.name)
    is_locked = locked

    def idle(self):
        assert self.got
        try:
            next(self.gen)
        except StopIteration:
            raise AZRPCTimeout('Stream closed while idling')

    def __enter__(self):
        return self.acquire()

    def __exit__(self, type, value, traceback):
        if self.got:
            self.release()


@contextmanager
def get_lock(name, try_=False, target=DEFAULT_TARGET):
    """Acquires or tries to acquire the lock. Returns `True` when the lock is
    acquired.
    """
    lock = Lock(name, try_, target=target)
    with lock as got_lock:
        yield got_lock


def locked(name, target=DEFAULT_TARGET):
    return _is_locked.execute(target, name)
is_locked = locked
