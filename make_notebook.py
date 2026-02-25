import nbformat as nbf
import codecs

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}

# Markdown #1
md_intro = """# Анализатор курсов валют (ЦБ РФ)

Этот Jupyter Notebook (наравне с HTML-версией) представляет собой демонстрацию логики проекта **"BookSense: Currency Market Intelligence"**. 

Полная версия проекта содержит графический дашборд на `Streamlit`, фоновый планировщик сбора данных `schedule`, парсер для HTTP-запросов и Unit-тестирование (см. исходные `.py` файлы проекта).

В этом интерактивном блокноте мы продемонстрируем:
1. Выполнение парсинга с сайта ЦБ РФ.
2. Работу с исторической базой данных (за последние 3 года).
3. Аналитику (Pandas) и визуализацию графиков (Plotly).
"""

# Code #1
code_parse = """import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from IPython.display import display

# Парсер текущих курсов ЦБ РФ (cbr.ru)
URL = "https://cbr.ru/currency_base/daily/"
headers = {"User-Agent": "Mozilla/5.0"}
    
try:
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', class_='data')
    rows = table.find_all('tr')[1:]
    
    currency_data = []
    
    # Парсим структуру
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 5:
            units = int(cols[2].text.strip())
            name = cols[3].text.strip()
            rate = float(cols[4].text.strip().replace(',', '.'))
            
            # Приведение курса к стоимости 1-ой единицы валюты (!)
            actual_rate = rate / units
            
            currency_data.append({
                "Валюта": name,
                "Курс (₽)": float(f"{actual_rate:.4f}")
            })
    
    df_parsed = pd.DataFrame(currency_data)
    print("Успешно спарсено", len(df_parsed), "валют. Пример первых 5-ти:")
    display(df_parsed.head(5))

except Exception as e:
    print("Ошибка соединения", e)
"""

md2 = "## Аналитика исторической базы\nПрочитаем и агрегируем базу данных из CSV файла, которая была собрана в рамках проекта, отфильтровав ее по ТОП-5 популярным валютам."

code_history = """# Читаем файл, собранный фоновым планировщиком
df = pd.read_csv('data/currency_history.csv')
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

popular_currencies = [
    "Доллар США", "Евро", "Китайский юань", 
    "Фунт стерлингов Соединенного королевства", "Казахстанский тенге"
]
df_filtered = df[df['Currency_Name'].isin(popular_currencies)].copy()

# Агрегация по месяцам (берем последнее значение каждого месяца)
df_filtered.loc[:, 'YearMonth'] = df_filtered['Timestamp'].dt.to_period('M')
df_monthly = df_filtered.sort_values('Timestamp').groupby(['Currency_Name', 'YearMonth']).last().reset_index()
# Возвращаем Timestamp для правильного отображения на графике
df_monthly['Timestamp'] = df_monthly['YearMonth'].dt.to_timestamp(how='end')

print("Агрегированные по месяцам исторические курсы:")
display(df_monthly[['Timestamp', 'Currency_Name', 'Rate_to_RUB']].head(10))"""

md3 = "## Графическая визуализация (Plotly)\nПостроим интерактивный график ежемесячного изменения курсов топовых валют."

code_plotly = """# Создание линейного графика Plotly
fig = px.line(df_monthly, x="Timestamp", y="Rate_to_RUB", color="Currency_Name", markers=True, 
              labels={"Timestamp": "Время снятия показателей (Конец месяца)", "Rate_to_RUB": "Курс к рублю (₽)", "Currency_Name": "Валюта"},
              title="Динамика курсов топовых валют за последние 3 года (ежемесячно)")

# В Jupyter отображаем с помощью show
fig.show()"""

md4 = "## Итоговая статистика (Агрегация Pandas)\nСчитаем минимальные, максимальные и средние значения курса по каждой валюте за годы наблюдений."

code_stats = """# Анализ информации через агрегацию DataFrame
stats = df_monthly.groupby("Currency_Name")["Rate_to_RUB"].agg(['min', 'max', 'mean', 'count']).reset_index()
stats.columns = ["Валюта", "Минимум (₽)", "Максимум (₽)", "Среднее (₽)", "Месяцев истории"]
stats["Среднее (₽)"] = stats["Среднее (₽)"].round(4)

print("Глобальная статистика курсов (описание данных):")
display(stats)"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(md_intro),
    nbf.v4.new_code_cell(code_parse),
    nbf.v4.new_markdown_cell(md2),
    nbf.v4.new_code_cell(code_history),
    nbf.v4.new_markdown_cell(md3),
    nbf.v4.new_code_cell(code_plotly),
    nbf.v4.new_markdown_cell(md4),
    nbf.v4.new_code_cell(code_stats),
]

with open('Project_Currency_Analytics.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print('Notebook Project_Currency_Analytics.ipynb создан успешно!')
