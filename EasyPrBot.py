import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
from IPython.display import HTML

class EasyPrBot_Filters:
  def __init__(self, main_link = 'https://easyprbot.com/api/',
               category_sublink = 'core/data/themes/',
               blogers_sublink = 'reviews'):
    self.main_link = main_link
    self.category_sublink = category_sublink
    self.blogers_sublink = blogers_sublink
    self.categories = {}
    self.formats = {'Сторис': 1,
                    'Фото-пост': 2,
                    'Видео-пост': 3,
                    'Пост+сторис': 4,
                    'Гив': 5}

    self.parse_meta = {'Бартер': 'barter', 'Взаимопиар': 'together'}
    self.blogers_json = None
    self.blogers_df = None
    self.all_pages_blogers_df = None
    self.num = None
    self.total_pages = None


  #TO-DO: automate getting formats of ads

  def get_categories(self):
    result = requests.get(self.main_link+self.category_sublink)
    result = result.json()['results']
    for category in result:
      self.categories[category['name'].lower()] = category['id']
    return self.categories

  def format_bloger(self, bloger):
    for field in ['ad_type', 'type', 'customer', 
                  'customer_kind', 'id', 'item', 'reviews_count_advertiser',
                  'paid_off', 'liked', 'show_text', 'price_meta', 
                  'liked_by_viewer']:
      del bloger[field]

    bloger['customer_tags'] = ';'.join(list(map(lambda x: x['name'], 
                                                bloger['customer_tags'])))
    if bloger['advertiser_blogger'] is not None:
      nickname = bloger['advertiser_blogger']['instaname']
      
    else:
      nickname = bloger['advertiser']
    bloger['profile_link'] = f'https://www.instagram.com/{nickname}'
    del bloger['advertiser_blogger']

    return bloger

  def format_blogers_json(self, blogers_json):
    blogers_json = list(map(self.format_bloger, blogers_json))
    blogers_df = pd.DataFrame(blogers_json)
    return blogers_json, blogers_df

  def save_blogers_to_file(self, blogers, filename):
    blogers_save = blogers.copy()
    blogers_save['profile_link'] = blogers_save['profile_link'].apply(
        lambda x: f'=HYPERLINK("{x}", "{x}")')
    blogers_save.to_excel(filename)

  def get_blogers(self, query, save = True, filename = 'podbor.xlsx'):
    self.query = self.process_query(**query)
    num, total_pages, bloger_info = self.filter_blogers()
    self.num = num
    self.total_pages = total_pages
    print(f'Obtained {num} blogers in current search')
    self.blogers_json, self.blogers_df = self.format_blogers_json(bloger_info)
    if save:
      self.save_blogers_to_file(self.blogers_df, filename)
    return self.blogers_df

  def filter_blogers(self):
    result = requests.get(self.main_link+self.blogers_sublink, params = self.query)
    result = result.json()
    num = result['count']
    total_pages = result['total_pages']
    return num, total_pages, result['results']

  def process_query(self, page_num = 1,
                    num_blogers_per_page = 100, 
                    min_price = None, #type: int
                    max_price = None, #type: int
                    bloger_categories = None, #type: List[str]
                    min_auditory_arrival = None, #type: int
                    max_auditory_arrival = None, #type: int
                    min_price_per_follower = None, #type: int
                    max_price_per_follower = None, #type: int
                    blogers_with_stats = None, #type: bool
                    barter = None, #type: bool
                    vsaimopiar = None, #type: bool
                    ad_type = None, #type: str
                    ):
    query = {'page': str(page_num),
         'page_size': str(num_blogers_per_page),
         'rate': '0',
         'mode': 'all',
         'customer_kind': 'blogger',
         'deleted_reviews': 'false',
         'format': 'json'}

    if min_price is not None:
      query['price_min'] = str(min_price)
    if max_price is not None:
      query['price_max'] = str(max_price)

    if min_auditory_arrival is not None:
      query['arrival_min'] = str(min_auditory_arrival)
    if max_auditory_arrival is not None:
      query['arrival_max'] = str(max_auditory_arrival)

    if min_price_per_follower is not None:
      query['price_per_one_min'] = str(min_price_per_follower)
    if max_price_per_follower is not None:
      query['price_per_one_max'] = str(max_price_per_follower)

    if bloger_categories is not None:
      bloger_categories = list(map(lambda x: str(self.categories[x.lower()]), 
                                   bloger_categories))
      query['tags'] = bloger_categories

    if barter is not None and vsaimopiar is not None:
      if barter and vsaimopiar:
        query['price_meta'] = [self.parse_meta['Бартер'], 
                               self.parse_meta['Взаимопиар']]
    elif barter:
      query['price_meta'] = self.parse_meta['Бартер']
    elif vsaimopiar:
      query['price_meta'] = self.parse_meta['Взаимопиар']

    if ad_type is not None:
      query['type'] = str(ad_type)

    return query

  def to_page(self, page):
    self.query['page'] = page
    num, total_pages, bloger_info = self.filter_blogers()
    self.blogers_json, self.blogers_df = self.format_blogers_json(bloger_info)
    return self.blogers_df

  def get_all_pages(self, query, save = False, filename = 'database.xlsx'):
    self.query = self.process_query(**query)
    num, total_pages, bloger_info = self.filter_blogers()
    self.num = num
    self.total_pages = total_pages
    print(f'Obtained {num} blogers in current search')
    if num == 0:
      print('Try other parameters')
      return None
    all_pages = []
    for i in tqdm(range(1, self.total_pages+1)):
      self.query['page'] = i
      _, _, bloger_info = self.filter_blogers()
      _, blogers_df = self.format_blogers_json(bloger_info)
      all_pages.append(blogers_df)
    self.all_pages_blogers_df = pd.concat(all_pages)
    self.all_pages_blogers_df = self.all_pages_blogers_df.reset_index()
    if save:
      today_date = datetime.today().strftime('%Y_%m_%d')
      self.save_blogers_to_file(self.all_pages_blogers_df, f'database_{today_date}.xlsx')
    return self.all_pages_blogers_df

  def show_table(self, data_df):
    data_df = data_df.copy()
    data_df['profile_link'] = data_df['profile_link'].apply(lambda x: f'<a href="{x}">{x}</a>')
    return HTML(data_df.to_html(escape=False))