import asyncio

from common.mutable_state_flow import MutableStateFlow


async def ui(name: str, flow: MutableStateFlow) -> None:
    async for v in flow:
        print(name, v)


async def main() -> None:
    state = MutableStateFlow(0)
    print('Starting A')
    asyncio.create_task(ui('A', state))
    await asyncio.sleep(0.1)
    print('Starting B')
    asyncio.create_task(ui('B', state))
    for n in range(1, 4):
        print('Emitting', n)
        await state.emit(n)
        await asyncio.sleep(0.1)


asyncio.run(main())
