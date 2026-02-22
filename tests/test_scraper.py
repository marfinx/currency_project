# pyre-ignore-all-errors
import pytest
from scraper import fetch_exchange_rates
import pandas as pd

def test_fetch_exchange_rates_success():
    """Тестирование функции парсера, ожидаем список с записями о курсах."""
    data = fetch_exchange_rates()
    # Проверка, что парсер не упал (например из-за изменения HTML)
    assert data is not None, "Парсер вернул None. Ошибка соединения или изменения структуры HTML."
    assert type(data) is list, "Ожидался список словарей."
    
    if len(data) > 0:
        first_item = data[0]
        # Проверка структуры данных
        assert "Timestamp" in first_item
        assert "Currency_Name" in first_item
        assert "Rate_to_RUB" in first_item
        # Проверка типов данных (что не записали строку вместо float)
        assert isinstance(first_item["Currency_Name"], str)
        assert isinstance(first_item["Rate_to_RUB"], float)

def test_pandas_dataframe_creation():
    """Проверка, что спарсенные структуры корректно конвертируются в DataFrame."""
    dummy_data = [
        {"Timestamp": "2024-01-01 12:00:00", "Currency_Name": "Доллар США", "Rate_to_RUB": 90.5}
    ]
    df = pd.DataFrame(dummy_data)
    # Проверка, что pandas смог обработать наши словари
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]["Currency_Name"] == "Доллар США"
