# pyre-ignore-all-errors
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import os

DATA_FILE = "data/currency_history.csv"

popular_currencies = [
    "Доллар США", "Евро", "Китайский юань", "Фунт стерлингов Соединенного королевства",
    "Швейцарский франк", "Японская иена", "Казахстанский тенге", "Белорусский рубль",
    "Турецкая лира", "Индийская рупия", "Дирхам ОАЭ", "Армянский драм", 
    "Грузинский лари", "Узбекский сум", "Польский злотый", "Шведская крона", 
    "Австралийский доллар", "Канадский доллар", "Сингапурский доллар", "Южнокорейская вона"
]

def fetch_cbr_history(years=3):
    today = datetime.now()
    start_date = today - timedelta(days=years*365)
    
    date_req1 = start_date.strftime("%d/%m/%Y")
    date_req2 = today.strftime("%d/%m/%Y")
    
    print(f"Начинаем загрузку историй за {years} года...")
    
    valutes_map = {
        "Доллар США": "R01235",
        "Евро": "R01239",
        "Китайский юань": "R01375",
        "Фунт стерлингов Соединенного королевства": "R01035",
        "Швейцарский франк": "R01775",
        "Японская иена": "R01820",
        "Казахстанский тенге": "R01335",
        "Белорусский рубль": "R01090B",
        "Турецкая лира": "R01700J",
        "Индийская рупия": "R01270",
        "Дирхам ОАЭ": "R01230",
        "Армянский драм": "R01060",
        "Грузинский лари": "R01210",
        "Узбекский сум": "R01717A",
        "Польский злотый": "R01565",
        "Шведская крона": "R01770",
        "Австралийский доллар": "R01010",
        "Канадский доллар": "R01350",
        "Сингапурский доллар": "R01625",
        "Южнокорейская вона": "R01815"
    }

    all_data = []
    
    for name in popular_currencies:
        val_id = valutes_map.get(name)
        if not val_id:
            print(f"Не найден ID для: {name}")
            continue
            
        dyn_url = f"http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date_req1}&date_req2={date_req2}&VAL_NM_RQ={val_id}"
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            dyn_resp = requests.get(dyn_url, headers=headers, timeout=10)
            dyn_tree = ET.fromstring(dyn_resp.content)
        except Exception as e:
            print(f"Ошибка при загрузке {name}: {e}")
            continue

            
        count = 0
        for record in dyn_tree.findall("Record"):
            date_str = record.attrib['Date'] # "dd.mm.yyyy"
            nominal = int(record.find("Nominal").text)
            value = float(record.find("Value").text.replace(',', '.'))
            rate = value / nominal
            
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            formatted_date = dt.strftime("%Y-%m-%d 12:00:00")
            
            all_data.append({
                "Timestamp": formatted_date,
                "Currency_Name": name,
                "Rate_to_RUB": round(rate, 4)
            })
            count += 1
            
        print(f"[{name}] Загружено записей: {count}")

    if all_data:
        df_new = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(os.path.abspath(DATA_FILE)), exist_ok=True)
        if os.path.exists(DATA_FILE):
            try:
                df_existing = pd.read_csv(DATA_FILE)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                # Удаляем дубликаты по дате и названию
                df_combined = df_combined.drop_duplicates(subset=["Timestamp", "Currency_Name"], keep='last')
                df_combined = df_combined.sort_values(by="Timestamp")
                df_combined.to_csv(DATA_FILE, index=False)
            except Exception:
                df_new.to_csv(DATA_FILE, index=False)
        else:
            df_new.sort_values(by="Timestamp").to_csv(DATA_FILE, index=False)
        print("Исторические данные успешно сохранены в CSV!")

if __name__ == "__main__":
    fetch_cbr_history(3)
