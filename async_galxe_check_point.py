import asyncio
import csv
import random
from functools import wraps
from typing import Callable

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

RETRY = 3  # Кол-во попыток при неудачно запросе
GALXE_CAMPAIGN = 'Linea'  # Просто пишет название компании https://galxe.com/Linea/campaigns

PROXY_ON = False  # False если без прокси, True если с прокси.
INPUT_FILE_NAME = 'wallet.txt'  # Название файла, где кошельки.
PROXIES_FILE_NAME = 'proxies.txt'  # Название файла, где прокси.
SAVE_FILE_NAME = 'result.csv'  # Название файла результата.

with open(INPUT_FILE_NAME, 'r', encoding='utf-8') as f:
    addresses = f.read().split()

with open('proxies.txt', 'r', encoding='utf-8') as f:
    proxies = f.read().split()


def retry_request(retry_count: int):
    def decorator(func: Callable):
        @wraps(wrapped=func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retry_count:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    print(f"Ошибка запроса. {e}. Делаю попытку... (Attempt {attempt + 1}/{retry_count})")
                    attempt += 1
                    await asyncio.sleep(1)
            raise Exception(f"Request failed after {retry_count} attempts.")
        return wrapper
    return decorator


@retry_request(retry_count=RETRY)
async def api_request(alias: str,
                      address: str) -> dict | None:
    payload = {
        'operationName': 'SpaceAccessQuery',
        'variables': {
            'alias': alias,
            'address': address,
        },
        'query': 'query SpaceAccessQuery($id: Int, $alias: String, $address: String!) '
                 '{\n  space(id: $id, alias: $alias) '
                 '{\n    id\n    isFollowing\n    discordGuildID\n    discordGuildInfo\n    status\n    '
                 'isAdmin(address: $address)\n    unclaimedBackfillLoyaltyPoints(address: $address)\n    '
                 'addressLoyaltyPoints(address: $address) '
                 '{\n      id\n      points\n      rank\n      __typename\n    }\n    __typename\n  }\n}\n',

    }

    headers = {
        'origin': 'https://galxe.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    if PROXY_ON and proxies:
        connector = ProxyConnector.from_url(random.choice(proxies))
    else:
        connector = None

    async with ClientSession(connector=connector) as session:
        async with session.post(url='https://graphigo.prd.galaxy.eco/query',
                                headers=headers,
                                json=payload) as response:
            json_data = await response.json()

            points = json_data['data']['space']['addressLoyaltyPoints']['points']
            rank = json_data['data']['space']['addressLoyaltyPoints']['rank']

            print(f'Кошелек {address} - С баллами {points} - РАНК {rank}')
            return {
                "address": address,
                "points": int(points),
                "rank": None if rank == 99999 else int(rank)
            }


async def main():
    result = []

    async with asyncio.TaskGroup() as tg:
        for address in addresses:
            result.append(tg.create_task(api_request(address=address, alias=GALXE_CAMPAIGN)))

    with open(f'{SAVE_FILE_NAME}', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["address", "points", "rank"], delimiter=';')
        writer.writeheader()
        writer.writerows([i.result() for i in result])


if __name__ == '__main__':
    asyncio.run(main())
