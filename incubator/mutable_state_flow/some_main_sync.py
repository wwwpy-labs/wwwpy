import asyncio
import time

from .mutable_state_flow import MutableStateFlow


async def consumer(tag: str, flow: MutableStateFlow[int]):
    async for v in flow:
        print(tag, v)


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    flow = MutableStateFlow(0)

    tasks = [loop.create_task(consumer('A', flow))]
    loop.run_until_complete(asyncio.sleep(0.05))
    tasks.append(loop.create_task(consumer('B', flow)))

    for n in range(1, 4):
        # loop.run_until_complete(flow.emit(n))  # wait for emit to finish
        flow.try_emit(n)
        time.sleep(0.05)  # any sync work here

    loop.run_until_complete(asyncio.sleep(0.2))  # let collectors drain

    for t in tasks:  # clean shutdown
        t.cancel()
    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':
    main()
