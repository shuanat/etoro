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


def cookies_parse(response_cookies: str) -> dict:
    cookies_dict = {}
    cookies = response_cookies
    for cookie in str(cookies).split('\r\n'):
        cookie = cookie.split(' ')
        if len(cookie) > 1:
            cookie_list = cookie[1].split('=')
            if len(cookie_list) == 2:
                cookies_dict[cookie_list[0]] = cookie_list[1]
            elif len(cookie_list) > 2:
                cookies_dict[cookie_list[0]] = cookie_list[1]
                for i in range(len(cookie_list) - 2):
                    cookies_dict[cookie_list[0]] += '='
    return cookies_dict