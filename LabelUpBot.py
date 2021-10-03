from tqdm import tqdm
from telethon import TelegramClient
from sqlite3 import OperationalError
import pandas as pd
import time
import nest_asyncio
import asyncio
from bs4 import BeautifulSoup
import requests
from utils import df_to_excel

USERNAME = 'labelup_bot'
SESSION_NAME = 'Sender'


class LabelUpBot:
    def __init__(self, filename, num_of_first_bloger, num_of_last_bloger, api_hash, api_id, myphone) -> None:
        self.filename = filename
        self.num_of_first_bloger = num_of_first_bloger
        self.num_of_last_bloger = num_of_last_bloger
        self.api_hash = api_hash
        self.api_id = api_id
        self.myphone = myphone

    def prepare_data(self, myfile):
        content = myfile.file.read()
        chosen_blogers = pd.read_excel(content)
        if self.num_of_last_bloger == -1:
            blogers = chosen_blogers['profile_link'].values[self.num_of_first_bloger:]
        else:
            blogers = chosen_blogers['profile_link'].values[self.num_of_first_bloger:self.num_of_last_bloger]
        return blogers

    async def send_message(self, sess_name, profile_link,  api_id, api_hash):
        try:
            async with TelegramClient(f'{sess_name}', api_id, api_hash) as client:
                if '__' in profile_link:
                    return sess_name, None, None
                # profile_link_escaped = profile_link.replace("__", "\__")
                await client.send_message(f'{USERNAME}', f'{profile_link}')
                # ^ note you need to use `await` in Jupyter
                # we are avoiding the `.sync` magic so it needs to be done by yourself
                profile_name = profile_link.split('/')
                if profile_name[-1] == '' or '?' in profile_name[-1]:
                    profile_name = profile_name[-2]
                else:
                    profile_name = profile_name[-1]
                time.sleep(5)
                async for message in client.iter_messages(f'{USERNAME}'):
                    if ' лимит ' in message.text:
                        return None, None, None
                    if profile_name in message.text and not message.out and 'добавлен на просчет' not in message.text:
                        try:
                            if message.buttons[0][0].text == 'Открыть полную статистику':
                                res_url = message.buttons[0][0].url
                            else:
                                res_url = None
                        except TypeError:
                            print(
                                'At the moment there is no info about bloger. Try again later')
                            return sess_name, None, None
                        return sess_name, message.text, res_url

                return sess_name, None, None

        except OperationalError:
            sess_name += '_1'
            print('rerun function')
            return sess_name, None, None

    def loops(self, name, profile_link,  api_id, api_hash):
        loop = asyncio.get_event_loop()
        name, res_text, res_url = loop.run_until_complete(
            self.send_message(name, profile_link,  api_id, api_hash))
        return name, res_text, res_url

    # отдает словарь вида инстаграм - линк лейблап
    def LU_get_short_data(self, blogers):
        global SESSION_NAME
        res = {}
        nest_asyncio.apply()
        blogers = self.prepare_data(blogers)
        for bloger in tqdm(blogers):
            SESSION_NAME, res_text, res_url = self.loops(
                SESSION_NAME, bloger, self.api_id, self.api_hash)
            if SESSION_NAME is None:
                SESSION_NAME = 'Sender'
                return res
            if res_text is None:
                print(f'Bloger {bloger} wasn\'t processed')
            else:
                res[bloger] = res_url

        return res
    # parser

    def get_LU_full_info(self, blogers_dict):
        res_table = []
        for bloger in tqdm(blogers_dict):
            if blogers_dict[bloger] is None:
                continue
            res = self.get_data(blogers_dict[bloger])
            res_table.append(res)
        return df_to_excel(df=pd.DataFrame(res_table), filename = 'labelup.xlsx')
#
    def get_page_parse(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return response, soup

    def get_request_params(self, response, soup):
        session = response.cookies.get_dict()['session']
        csrf_token = soup.find("meta", attrs={'name':"csrf-token"})['content']
        return session, csrf_token
 # 
    def get_user_id(self, url):
        user_id = url.split('/')[-1]
        return user_id

    def create_cookies(self, session):
        cookies = {'session': f'{session}'}
        return cookies
#
    def create_header(self, csrf_token, url):
        headers = {
            'X-CSRF-Token': f'{csrf_token}',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://labelup.ru',
            'Referer': f'{url}'
                }
        return headers

    def create_body(self, user_id):
        body = f'{{"query_hash":"68663d1f590fb4c9cfaa7e651b3597898e31fd729cd6a55574c584d0dbfcf2f5","variables":"{{\\"guestToken\\":\\"{user_id}\\"}}"}}'
        return body

    def format_json_data(self, data_json):
        for gen_data in data_json['genders']:
            data_json[gen_data['index']+'_auditory'] = gen_data['percent']
        del data_json['demography']
        del data_json['genders']

        data_json['profile_link'] = data_json['link']
        del data_json['link']
        
        price_range_trans = {'From': 'min', 'To': 'max'}
        for price_cat in ['exclusive', 'post', 'stories']:
            for price_range in ['From', 'To']:
                if data_json['estimatedPrices'] is not None:
                    data_json[f'estimated_price_{price_cat}_{price_range_trans[price_range]}'] = \
                    data_json['estimatedPrices'][f'{price_cat}{price_range}']
                else:
                    data_json[f'estimated_price_{price_cat}_{price_range_trans[price_range]}'] = \
                    None
        del data_json['estimatedPrices']

        for periods in data_json['followersChanges']:
            period = periods['period']
            data_json[f'followers_period_{period}'] = periods['count']
        del data_json['followersChanges']

        if data_json['gender'] is not None:
            data_json['gender'] = data_json['gender']['index']

        if len(data_json['subjects']) > 0:
            data_json['subjects'] = ';'.join(list(map(lambda x: x['name'], data_json['subjects'])))
        else:
            data_json['subjects'] = None

        
        data_json['countries_stats'] = ';'.join(list(map(lambda x: x['name']+'_'+str(x['percent'])+'%', 
                                                data_json['geoFollowers']['countries'])))
        
        data_json['cities_stats'] = ';'.join(list(map(lambda x: x['name']+'_'+str(x['percent'])+'%', 
                                                data_json['geoFollowers']['locations'])))
        del data_json['geoFollowers']
        
        data_json['top_hastags'] = ';'.join(list(map(lambda x: x['value']+' '+str(x['count']), 
                                                data_json['hashtags'])))
        
        del data_json['hashtags']
        
        if data_json['location'] is not None:
            data_json['location'] = data_json['location']['name']

        del data_json['mentions']

        data_json['network'] = data_json['network']['name']

        for num_sub in data_json['popularity'].keys():
            data_json[f'num_followers_with_{num_sub}_followers'] = \
            data_json['popularity'][num_sub]['count']
        del data_json['popularity']

        data_json['posts_photos'] = '\n'.join(list(map(lambda x: x['thumbnails']['high'][16:], 
                                                    data_json['posts']['last'])))
        del data_json['posts']


        for reach_type in data_json['reachabilityDetails']:
            data_json[f'reachability_{reach_type}'] = \
            data_json['reachabilityDetails'][reach_type]['count']
        del data_json['reachabilityDetails']

        if len(data_json['statistics'])>0:
            for stats in data_json['statistics'][-1]:
                data_json[stats] = data_json['statistics'][-1][stats]
        else:
            for stats in ['followersCount', 'followsCount', 'mediaCount', 'averageLikesCount', 'createdAt']:
                data_json[stats] = None
        del data_json['statistics']

        data_json['type'] = data_json['type']['index']

        data_json['LQI'] = data_json['score']
        del data_json['score']

        return data_json



    def get_data(self, url):
        response, soup = self.get_page_parse(url)
        session, csrf_token = self.get_request_params(response, soup)
        user_id = self.get_user_id(url)

        cookies = self.create_cookies(session)
        headers = self.create_header(csrf_token, url)
        body = self.create_body(user_id)

        response_res = requests.post('https://labelup.ru/graphql/query', 
                                headers=headers, cookies = cookies, data=body)
        
        data_json = response_res.json()['data']['account']
        data_json = self.format_json_data(data_json)
        return data_json

    
