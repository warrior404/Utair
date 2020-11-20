from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import time
import re

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
driver.get('http://www.krasnodar.vybory.izbirkom.ru/region/krasnodar?action=ik')

# Ожидание подгрузки элементов на странице
t = True
while t:
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'jstree-anchor')))
        t = False
        print('Данные прогружены\n')
    except TimeoutException:
        print('Данные не прогрузились\n')

# Найдем элементы в папке 'Избирательная комиссия Краснодарского края'
lst = driver.find_elements_by_class_name('jstree-closed')
tik_lst = [i.text for i in lst]
print(f'Длина списка ТИК: {len(tik_lst)}\nНаименования ТИК: {tik_lst}\n')

# Цикл получения списка всех таблиц по составу УИК в каждом ТИК
tables_lst = []
count = -1
new_tik_lst = lst
for tik in lst:
    count += 1

    # Наименование тика
    tik_name = tik_lst[count]

    # Раскроем ТИК на УИКи
    print(f'Vsego TIK: {len(driver.find_elements_by_class_name("jstree-closed"))}')
    for i in driver.find_element_by_class_name('jstree-children').find_element_by_class_name('jstree-children').find_elements_by_class_name('jstree-closed'):
        if i.text == tik_name:
            i.find_element_by_class_name('jstree-anchor').click()
            break

    # Дождемся открытия
    t = True
    while t:
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'jstree-leaf')))
            t = False
        except TimeoutException:
            pass

    # Список всех УИК в ТИКе
    time.sleep(0.1)
    uik_lst = driver.find_elements_by_class_name('jstree-leaf')
    time.sleep(0.1)
    uik_names = [i.text for i in uik_lst]
    print(f'Длина списка УИК: {len(uik_names)}\nНаименования УИК: {uik_names}\n')

    # Цикл обработки всех УИК в ТИКе
    c = -1
    for uik in uik_lst:
        c += 1

        # Наименование УИК
        uik_name = uik_names[c]

        # Дождемся открытия
        t = True
        while t:
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'jstree-leaf')))
                t = False
            except TimeoutException:
                pass

        # Кликнем на УИК
        driver.find_elements_by_class_name('jstree-leaf')[c].find_element_by_class_name('jstree-anchor').click()

        # Дождемся загрузки
        t = True
        while t:
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'jstree-clicked')))
                t = False
            except TimeoutException:
                pass

        # Получим весь текст со страницы
        full_page_text = driver.find_element_by_class_name('center-colm').text
        # print(f'FULL TEXT: {full_page_text}\n\n-----')

        # Получим наименования из текста
        page_uik_name = driver.find_element_by_class_name('center-colm').text.split('\n')[0]
        # print(uik_name, page_uik_name)

        # Убедимся, что номера УИК совпадают
        if uik_name == page_uik_name:
            # Найдем данные таблицы
            table_text = re.split(r'Члены избирательной комиссии с правом решающего голоса', full_page_text)[1]

            # Получим список строк
            rows = table_text.split('\n')[2:]
            print(f'Всего строк в таблице: {len(rows)}\nСписок строк: {rows}\n')

            # Создание датафрейма
            mini_df = pd.DataFrame({'rows': rows[1:]})
            mini_df['ТИК'] = [tik_name for i in range(len(mini_df))]
            if len(uik_names) != 1:
                mini_df['УИК №'] = [uik_name.split('№')[1] for i in range(len(mini_df))]
            else:
                mini_df['УИК №'] = None
            mini_df['ФИО'] = mini_df['rows'].apply(lambda x: ' '.join(x.split(' ')[1:4])).astype(str)
            mini_df['Статус'] = mini_df['rows'].apply(lambda x: x.split(' ')[4]).astype(str)
            mini_df['Кем предложен в состав комиссии'] = mini_df['rows'].apply(lambda x: ' '.join(x.split(' ')[5:])).astype(str)
            mini_df = mini_df.drop(columns=['rows'])
            tables_lst.append(mini_df)
            # print(mini_df)
            print('Датафрейм по участку создан\n')
        print(f'{uik_name} Отработан\n')

    # Закроем список УИК
    closing_button = driver.find_element_by_class_name('jstree-children').find_element_by_class_name('jstree-children').find_element_by_class_name('jstree-ocl')
    closing_button.click()
    time.sleep(0.15)

    new_tik_lst = driver.find_elements_by_class_name('jstree-closed')

    print(f'{tik_name} Отработан\n')

print(f'Список таблиц сформирован. Длина: {len(tables_lst)}\n')

# Сложим все полученные таблицы в одну
df = pd.concat(tables_lst, ignore_index=True).reset_index(drop=True)
print(df)

# Сохраним файл в csv
df.to_csv('./parsed.csv', index=False)
