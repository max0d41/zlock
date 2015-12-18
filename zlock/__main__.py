from gevent.monkey import patch_all
patch_all()

import os
import logging

from gevent import sleep

from azrpc import AZRPCServer

from . import ZLOCK_PORT, rpc, stats, locks, waiting

logger = logging.getLogger(__name__)


STATS_INTERVAL = int(os.environ.get('STATS_INTERVAL', 10))


def main():
    logging.basicConfig(level=logging.INFO)
    AZRPCServer(rpc)
    logger.info('Listening on port %s', ZLOCK_PORT)
    try:
        while True:
            logger.info(
                'Stats: '
                '{requests} requests, {already_locked} already_locked, '
                '{waiting} waiting, {active} active, '
                '{try_failed} try_failed, {acquired} acquired, {released} released, '
                '{timeout} timeout, {unexpected} unexpected, '
                '{failed} failed, {failed_timeout} failed_timeout, '
                '{exceptions} exceptions'.format(active=len(locks), waiting=len(waiting), **stats))
            sleep(STATS_INTERVAL)
    except KeyboardInterrupt:
        pass

main()
