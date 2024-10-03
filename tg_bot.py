import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

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
    
    # Таблица для фейковых новостей
    c.execute('''
        CREATE TABLE IF NOT EXISTS fake_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fake_content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Функция для парсинга новостей
   def parse_news(url):
       logging.info(f'Парсинг новостей с {url}')
       try:
           response = requests.get(url, timeout=10)
           soup = BeautifulSoup(response.content, 'xml')
           items = soup.find_all('item')
           news_list = []

           for item in items:
               title = item.find('title').text if item.find('title') else 'Без заголовка'
               content = item.find('description').text if item.find('description') else 'Без описания'
               link = item.find('link').text if item.find('link') else 'Без ссылки'
               news_list.append((title, content, link))

           return news_list
       except requests.exceptions.Timeout:
           logging.error(f'Превышен лимит времени ожидания для {url}')
           return []
       except requests.exceptions.RequestException as e:
           logging.error(f'Ошибка при запросе {url}: {e}')
           return []
   

# Функция для сохранения новостей в базу данных
def save_to_db(news_list):
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    for news in news_list:
        c.execute('INSERT INTO news (title, content, source) VALUES (?, ?, ?)', news)
    
    conn.commit()
    conn.close()
    logging.info(f'{len(news_list)} новостей добавлено в базу данных.')

# Функция для проверки новостей на фейковость
def check_for_fakes(news_list):
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    c.execute("SELECT fake_content FROM fake_news")
    fake_news_list = c.fetchall()
    fake_news_list = [item[0] for item in fake_news_list]

    checked_news = []
    for title, content, source in news_list:
        if any(fake in content for fake in fake_news_list):
            checked_news.append((title, content, source, 'Фейк'))
        else:
            checked_news.append((title, content, source, 'Достоверна'))
    
    conn.close()
    return checked_news

# Команда для бота: получение новостей
async def get_news(update: Update, context):
    urls = [
        'http://rss.cnn.com/rss/edition.rss',
        'http://feeds.bbci.co.uk/news/rss.xml',
        'https://www.reutersagency.com/feed/?best-topics=rss'
    ]

    all_news = []
    for url in urls:
        news_list = parse_news(url)
        all_news.extend(news_list)

    save_to_db(all_news)
    checked_news = check_for_fakes(all_news)
    
    message = ""
    for news in checked_news[:5]:  # Ограничимся 5 новостями
        title, content, source, status = news
        message += f"Заголовок: {title}\nСтатус: {status}\nИсточник: {source}\n\n"
    
    await update.message.reply_text(message if message else "Новостей нет.")

# Основная функция
def main():
    create_database()
    
    # Настройка Telegram бота
    app = ApplicationBuilder().token('7900571114:AAE2egENPGPEl_hTxG_GwakAd8vRhjqBhqs').build()
    
    # Команда /news для получения новостей
    app.add_handler(CommandHandler("news", get_news))
    
    app.run_polling()
    response = requests.get(url, timeout=10)
   

if __name__ == '__main__':
    main()
