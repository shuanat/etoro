import time
import random


def device_id() -> str:
    pattern = "xxxxtxxx-xxxx-4xxx-yxxx-xxxxxxtxxxxx"
    pattern = pattern.replace('t', hex(int(time.time()) % 16).replace('0x', ''))
    pattern_list = list(pattern)
    for key, symblol in enumerate(list(pattern_list)):
        if symblol == 'x' or symblol == 'y':
            n = 16 * random.random()
            if n:
                n /= 3
            else:
                n = 8
            pattern_list[key] = hex(int(n)).replace('0x', '')
    return "".join(pattern_list)
