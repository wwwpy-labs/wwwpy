from remote import rpc

from wwwpy.server.conv import default_project


async def send_message_to_all(msg: str) -> str:
    for client in default_project().websocket_pool.clients:
        client.rpc(rpc.Rpc).new_message(msg)
    return 'done'
