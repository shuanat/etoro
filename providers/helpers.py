import time
import random


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