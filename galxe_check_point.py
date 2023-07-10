import requests
from pyuseragents import random as random_useragent
 
RETRY = 3 #кол. попыток при неудачно запросе
GALXE_CAMPANING = 'Linea' # Просто пишет название компании https://galxe.com/Linea/campaigns

PROXY_ON = True # False если без прокси, True если с прокси
PROXY = 'login:pass@ip:port' #прокси в формате 'login:pass@ip:port', если прокси PROXY_ON = True
SAVE_FILE_NAME = 'result.csv' #название файла результата
INPUT_FILE_NAME = 'wallet.txt' #Название файла где кошельки


proxies = {"http":f"http://{PROXY}",
           "https":f"http://{PROXY}"}

def check_wallet(address,alias,popitka=0):
    try:
        headers = {
            'authority': 'graphigo.prd.galaxy.eco',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://galxe.com',
            'user-agent': random_useragent(),
        }

        json_data = {
            'operationName': 'SpaceAccessQuery',
            'variables': {
                'alias': alias,
                'address': address.lower(),
            },
            'query': 'query SpaceAccessQuery($id: Int, $alias: String, $address: String!) {\n  space(id: $id, alias: $alias) {\n    id\n    isFollowing\n    discordGuildID\n    discordGuildInfo\n    status\n    isAdmin(address: $address)\n    unclaimedBackfillLoyaltyPoints(address: $address)\n    addressLoyaltyPoints(address: $address) {\n      id\n      points\n      rank\n      __typename\n    }\n    __typename\n  }\n}\n',
        }

        if PROXY_ON:
            response = requests.post('https://graphigo.prd.galaxy.eco/query', headers=headers, json=json_data,proxies=proxies)
        else:
            response = requests.post('https://graphigo.prd.galaxy.eco/query', headers=headers, json=json_data)

        point = response.json()['data']['space']['addressLoyaltyPoints']['points']
        rank = response.json()['data']['space']['addressLoyaltyPoints']['rank']
        print(f'Кошелек {address} - С баллами {point} - РАНК {rank}')
        return point,rank

    except Exception as e:
        if popitka < RETRY:
            print('Ошибка запроса',e,'Делаю попытку',popitka+1)
            check_wallet(address,alias,popitka=popitka+1)
        else:
            return 0,0

with open(INPUT_FILE_NAME, "r", encoding='utf-8' ) as f:
    wallet_list = [row.strip() for row in f]


for wallet in wallet_list:
    try:
        points,rank = check_wallet(wallet,GALXE_CAMPANING)

        with open(SAVE_FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(f"{wallet};{rank};{points}\n")
    except Exception as er:
        with open(SAVE_FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(f"{wallet};ошибка\n")





