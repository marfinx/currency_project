# pyre-ignore-all-errors
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

URL = "https://cbr.ru/currency_base/daily/"
DATA_FILE = "data/currency_history.csv"

def fetch_exchange_rates():
    """Отправляет запрос на сайт ЦБ РФ и парсит таблицу с курсами."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения данных: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', class_='data')
    if not table:
        print("Таблица с курсами не найдена на странице.")
        return None
        
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок
    
    currency_data = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 5:
            units = int(cols[2].text.strip())
            name = cols[3].text.strip()
            rate_str = cols[4].text.strip().replace(',', '.')
            rate = float(rate_str)
            
            # Приводим курс к стоимости 1 единицы валюты (ЦБ иногда отдает за 10, 100 единиц)
            actual_rate = float(rate) / float(units)
            
            currency_data.append({
                "Timestamp": current_time,
                "Currency_Name": name,
                "Rate_to_RUB": float(f"{actual_rate:.4f}")
            })
            
    return currency_data

def save_to_csv(data, filename=DATA_FILE):
    """Сохраняет спарсенные данные в CSV-файл."""
    if not data:
        print("Нет данных для сохранения.")
        return
        
    df_new = pd.DataFrame(data)
    
    # Если файл уже существует, добавляем новые строки к старым (сохраняем историю)
    if os.path.exists(filename):
        df_existing = pd.read_csv(filename)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.drop_duplicates(inplace=True)
        df_combined.to_csv(filename, index=False)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        df_new.to_csv(filename, index=False)
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Данные сохранены в {filename}")

if __name__ == "__main__":
    rates = fetch_exchange_rates()
    if rates:
        save_to_csv(rates)
