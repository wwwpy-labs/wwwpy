from __future__ import annotations

import logging

from wwwpy.websocket import WebsocketPool, PoolEvent

logger = logging.getLogger(__name__)


def _warning_on_multiple_clients(websocket_pool: WebsocketPool):
    def pool_before_change(event: PoolEvent):
        client_count = len(websocket_pool.clients)
        if client_count > 1:
            logger.warning(f'WARNING: more than one client connected, total={client_count}')
        else:
            logger.warning(f'Connected client count: {client_count}')

    websocket_pool.on_after_change.append(pool_before_change)


