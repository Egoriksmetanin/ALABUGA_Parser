import requests
from bs4 import BeautifulSoup
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Функция для создания базы данных и таблицы
def create_database():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    # Таблица для новостей
    c.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT
        )
    ''')
    
    # Таблица для хранения фейковых новостей
    c.execute('''
        CREATE TABLE IF NOT EXISTS fake_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fake_content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Функция для парсинга новостей из RSS-ленты
def parse_news(url):
        logging.info(f'Парсинг новостей с {url}')
        response = requests.get(url)
        
        # Используем lxml для парсинга RSS
        soup = BeautifulSoup(response.content, 'xml')  
        items = soup.find_all('item')  # RSS использует тег <item> для новостей
        news_list = []

        for item in items:
            title = item.find('title').text if item.find('title') else 'Без заголовка'
            content = item.find('description').text if item.find('description') else 'Без описания'
            link = item.find('link').text if item.find('link') else 'Без ссылки'
            
            logging.info(f'Заголовок: {title}, Описание: {content}, Ссылка: {link}')
            
            news_list.append((title, content, link))

        return news_list

# Функция для сохранения новостей в базу данных
def save_to_db(news_list):
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    # Проверяем каждую новость и добавляем её в БД
    for news in news_list:
        c.execute('INSERT INTO news (title, content, source) VALUES (?, ?, ?)', news)
    
    conn.commit()
    conn.close()
    logging.info(f'{len(news_list)} новостей добавлено в базу данных.')

# Функция для добавления фейковых новостей в базу
def add_fake_news(fake_news_list):
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    for fake_news in fake_news_list:
        c.execute('INSERT INTO fake_news (fake_content) VALUES (?)', (fake_news,))
    
    conn.commit()
    conn.close()

# Функция для проверки новостей на фейки
def check_for_fakes(news_list):
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    # Получаем все фейковые новости из БД
    c.execute("SELECT fake_content FROM fake_news")
    fake_news_list = c.fetchall()

    # Преобразуем список в удобный формат
    fake_news_list = [item[0] for item in fake_news_list]

    # Проверяем каждую новость на совпадение с фейковыми
    for title, content, source in news_list:
        if any(fake in content for fake in fake_news_list):
            logging.warning(f'Фейковая новость найдена: {title} (Источник: {source})')
        else:
            logging.info(f'Новость достоверна: {title}')

    conn.close()

# Основная функция
def main():
    create_database()
    
    # Пример фейковых новостей для демонстрации
    fake_news = ["фейковая новость 1", "фейковая новость 2"]
    add_fake_news(fake_news)
    
    # Список URL-адресов для парсинга
    urls = [
        'http://rss.cnn.com/rss/edition.rss',  # RSS-лента CNN
        'http://feeds.bbci.co.uk/news/rss.xml',  # RSS-лента BBC
        'https://www.reutersagency.com/feed/?best-topics=rss'  # RSS-лента Reuters
    ]
    
    all_news = []
    
    # Парсим новости с указанных URL
    for url in urls:
        news_list = parse_news(url)
        all_news.extend(news_list)
    
    # Сохраняем все новости в базу данных
    save_to_db(all_news)
    
    # Проверяем новости на фейковость
    check_for_fakes(all_news)
    
    logging.info("Парсинг завершён.")

if __name__ == '__main__':
    main()
