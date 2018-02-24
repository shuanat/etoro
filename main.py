import asyncio
import signal

from providers.tinkoff import TinkofProvider
from strategies.habr import HabrStrategy


def handler(loop):
    loop.remove_signal_handler(signal.SIGTERM)
    loop.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, handler, loop)
    strategy = HabrStrategy(loop)
    etoro = TinkofProvider(loop, strategy)
    try:
        loop.run_until_complete(etoro.execute())
    finally:
        loop.close()


if '__main__' == __name__:
    main()
