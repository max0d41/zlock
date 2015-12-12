from gevent.monkey import patch_all
patch_all()

import os
import logging

from gevent import sleep

from azrpc import AZRPCServer

from . import LISTEN_PORT, rpc, stats, _locks

logger = logging.getLogger(__name__)


STATS_INTERVAL = int(os.environ.get('STATS_INTERVAL', 10))

def main():
    logging.basicConfig(level=logging.INFO)
    AZRPCServer(rpc)
    logger.info('Listening on port %s', LISTEN_PORT)
    try:
        while True:
            logger.info(
                'Stats: {active} active / '
                '{requests} requests ({taken} taken, '
                '{acquired} acquired, {released} released, '
                '{timeout} timeout, {unexpected} unexpected) / '
                '{failed} failed, {failed_timeout} failed_timeout / '
                '{exceptions} exceptions'.format(active=len(_locks), **stats))
            sleep(STATS_INTERVAL)
    except KeyboardInterrupt:
        pass

main()
