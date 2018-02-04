import asyncio
import signal

from providers.etoro import EtoroProvider


def handler(loop):
    loop.remove_signal_handler(signal.SIGTERM)
    loop.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, handler, loop)
    etoro = EtoroProvider(loop)
    try:
        loop.run_until_complete(etoro.execute())
    finally:
        loop.close()

if '__main__' == __name__:
    main()
