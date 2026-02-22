# pyre-ignore-all-errors
import schedule
import time
from scraper import fetch_exchange_rates, save_to_csv

def job():
    print("Запуск задачи: сбор курсов валют...")
    data = fetch_exchange_rates()
    save_to_csv(data)

# Запускаем один раз сразу при старте скрипта
job()

# Настроено расписание на запуск каждые 5 часов
schedule.every(5).hours.do(job)

print("Планировщик запущен. Ожидание следующих запусков... Нажмите Ctrl+C для выхода.")
while True:
    schedule.run_pending()
    time.sleep(60) # Проверяем расписание каждую минуту
