from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import time
import re

from bs4 import BeautifulSoup

import pandas as pd


# Путь к профилю
profiles_path = '/home/zabavin/.config/google-chrome/'
profile_name = 'Profile 1'
# Путь к драйверу
chrome_driver_path = './drivers/chromedriver'

# Создание опций (запуск браузера с переданным профилем)
options = Options()
options.add_argument('--user-data-dir=' + profiles_path)
options.add_argument('--profile-directory=' + profile_name)

# Активация драйвера с заданными опциями
driver = webdriver.Chrome(chrome_driver_path, chrome_options=options)

# Заход на страницу
driver.set_page_load_timeout(10)
driver.get('http://www.krasnodar.vybory.izbirkom.ru/region/region/krasnodar?action=show&root=1&tvd=4234220141772&vrn=4234220141768&region=23&global=&sub_region=23&prver=2&pronetvd=1&vibid=4234220141772&type=381')
time.sleep(1)
input('Введите капчу')
time.sleep(1)

# Создадим суп из html
page = driver.page_source
sp = BeautifulSoup(page, 'lxml')
scores_array = {}

# Получим словарь по ОИО. {Key (название ОИО): Value (ссылка на таблицу)}
c1 = 0
oio_dct = {}
for oio_element in sp.find_all('a'):
    c1 += 1
    if c1 > 10:
        oio_dct[oio_element.text] = oio_element.get('href')
print(f'Словарь таблиц сформирован: {oio_dct}\n')

# Цикл парсинга таблиц на основе сформированного словаря
mini_df_lst = []
for oio in oio_dct.keys():
    # Основные параметры каждого oio
    oio_table_link = oio_dct[oio]
    oio_name = oio

    # Пройдем по ссылке для получения таблицы
    driver.get(oio_table_link)
    time.sleep(.75)

    # Создадим суп
    page = driver.page_source
    full_soup = BeautifulSoup(page, 'lxml')
    uik_cells = full_soup.findChildren('table')[9].findChildren(['tr'])[0]
    kprf_cells = full_soup.findChildren('table')[9].findChildren(['tr'])[18]

    # Выцепим необходимую информацию в нужном виде с помощью regex
    uik_lst = re.findall(r'УИК №\d+', uik_cells.text)
    value_lst = re.findall(r'\d+\.\d+%', kprf_cells.text)

    # Создадим мини-дф
    mini_df = pd.DataFrame({'OIO_name': [oio_name for i in range(len(value_lst))],
                            'Table_link': [oio_table_link for i in range(len(value_lst))],
                            'UIK': uik_lst,
                            'KPRF%': value_lst})
    mini_df_lst.append(mini_df)

# Получим финальный датафрейм
df = pd.concat(mini_df_lst, ignore_index=True)
print(df[['UIK', 'KPRF%']])

# Сохраним файл в csv
df.to_csv('./result.csv', index=False)
