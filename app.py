# pyre-ignore-all-errors
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Аналитика курсов валют", layout="wide")

DATA_FILE = "data/currency_history.csv"

@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    df = pd.read_csv(DATA_FILE)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

st.title("💱 Динамика курсов популярных валют к рублю")
st.markdown("В этом приложении визуализируются курсы валют ЦБ РФ. Данные собираются парсером автоматически каждые 5 часов.")

if st.button("🔄 Спарсить данные прямо сейчас"):
    from scraper import fetch_exchange_rates, save_to_csv
    st.info("Выполняется запрос к сайту ЦБ РФ...")
    rates = fetch_exchange_rates()
    save_to_csv(rates)
    st.cache_data.clear()
    st.success("Данные успешно обновлены!")
    st.rerun()

df = load_data()

if df.empty:
    st.warning("Нет сохраненных данных. Пожалуйста, нажмите кнопку выше или запустите `python scheduler_run.py`.")
else:
    # Оставляем только топ популярных валют для удобства
    popular_currencies = [
        "Доллар США", "Евро", "Китайский юань", "Фунт стерлингов Соединенного королевства",
        "Швейцарский франк", "Японская иена", "Казахстанский тенге", "Белорусский рубль",
        "Турецкая лира", "Индийская рупия", "Дирхам ОАЭ", "Армянский драм", 
        "Грузинский лари", "Узбекский сум", "Польский злотый", "Шведская крона", 
        "Австралийский доллар", "Канадский доллар", "Сингапурский доллар", "Южнокорейская вона"
    ]
    df_filtered = df[df['Currency_Name'].isin(popular_currencies)]
    
    # Резервный механизм, если вдруг ЦБ изменил названия (возьмем любые 20)
    if df_filtered.empty:
        currencies = df['Currency_Name'].unique()[:20]
        df_filtered = df[df['Currency_Name'].isin(currencies)]

    # Выделяем только актуальные данные (последний срез для КАЖДОЙ валюты отдельно)
    # Это исправляет баг, когда у некоторых валют последняя дата снятия была на день раньше
    latest_data = df_filtered.sort_values('Timestamp').groupby('Currency_Name').last().reset_index()

    # Настройка темной темы по умолчанию
    plotly_theme = "plotly_dark"
    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FFFFFF; }
        .stSelectbox label, .stMetric label { color: #FFFFFF !important; }
        .stButton>button { color: #FFFFFF !important; border-color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Кнопки скачивания в правом верхнем углу (через колонки)
    top_col1, top_col2, top_col3 = st.columns([6, 1, 1])
    with top_col2:
        # Скачивание CSV (в формате для русского Excel: cp1251, разделитель точка с запятой)
        csv_data = latest_data.to_csv(index=False, sep=';', encoding='cp1251').encode('cp1251')
        st.download_button(
            label="Скачать CSV",
            data=csv_data,
            file_name="currency_data.csv",
            mime="text/csv",
        )
    with top_col3:
        # Скачивание JSON (красивое форматирование с отступами)
        json_data = latest_data.to_json(orient='records', force_ascii=False, indent=4)
        st.download_button(
            label="Скачать JSON",
            data=json_data,
            file_name="currency_data.json",
            mime="application/json",
        )
        
    st.markdown("---")

    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Меню")
        selected_currency = st.selectbox("Выберите валюту:", df_filtered['Currency_Name'].unique())
        
        curr_row = latest_data[latest_data['Currency_Name'] == selected_currency]
        if not curr_row.empty:
            st.metric(label=f"Текущий курс", value=f"{curr_row.iloc[0]['Rate_to_RUB']:.4f} ₽")
            st.caption(f"На момент: {curr_row.iloc[0]['Timestamp']}")
            
    with col2:
        st.subheader(f"📈 Динамика курса: {selected_currency} (Ежемесячно)")
        df_currency = df_filtered[df_filtered['Currency_Name'] == selected_currency].copy()
        
        # Агрегация по месяцам (берем последнее значение каждого месяца)
        df_currency.loc[:, 'YearMonth'] = df_currency['Timestamp'].dt.to_period('M')
        # Группируем по месяцу и берем последнюю запись месяца
        df_monthly = df_currency.sort_values('Timestamp').groupby('YearMonth').last().reset_index()
        # Возвращаем Timestamp для красивого отображения на графике
        df_monthly['Timestamp'] = df_monthly['YearMonth'].dt.to_timestamp(how='end')
        
        fig = px.line(df_monthly, x="Timestamp", y="Rate_to_RUB", markers=True, 
                      labels={"Timestamp": "Время снятия показателей (Конец месяца)", "Rate_to_RUB": "Курс к рублю (₽)"},
                      template=plotly_theme)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    col3, col4 = st.columns((2, 2))
    
    with col3:
        st.subheader("📊 Топ текущих курсов (в Рублях)")
        fig_bar = px.bar(latest_data.sort_values(by="Rate_to_RUB", ascending=False), 
                         x="Rate_to_RUB", y="Currency_Name", orientation='h',
                         labels={"Rate_to_RUB": "Курс", "Currency_Name": "Валюта"},
                         template=plotly_theme)
        fig_bar.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col4:
        st.subheader("📋 Статистика по валютам (на основе ежемесячной истории)")
        
        # Чтобы статистика была для всех валют по месяцам:
        df_filtered_monthly = df_filtered.copy()
        df_filtered_monthly.loc[:, 'YearMonth'] = df_filtered_monthly['Timestamp'].dt.to_period('M')
        df_all_monthly = df_filtered_monthly.sort_values('Timestamp').groupby(['Currency_Name', 'YearMonth']).last().reset_index()
        stats = df_all_monthly.groupby("Currency_Name")["Rate_to_RUB"].agg(['min', 'max', 'mean', 'count']).reset_index()

        stats.columns = ["Валюта", "Минимум (₽)", "Максимум (₽)", "Среднее (₽)", "Месяцев"]
        stats["Среднее (₽)"] = stats["Среднее (₽)"].round(4)
        st.dataframe(stats, height=500, use_container_width=True)
