import sys
import requests
import xml.etree.ElementTree as ET

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine


class CurrencyConverter(QObject):

    resultChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.rates = {}
        self.load_rates()

    def load_rates(self):
        try:
            response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            root = ET.fromstring(response.content)

            for valute in root.findall("Valute"):
                char_code = valute.find("CharCode").text
                value = float(valute.find("Value").text.replace(",", "."))
                nominal = int(valute.find("Nominal").text)

                rate = value / nominal
                self.rates[char_code] = rate

        except Exception as e:
            self.resultChanged.emit(f"Ошибка загрузки курсов: {e}")

    @pyqtSlot(str, str)
    def convert_currency(self, amount_text, currency_text):
        try:
            amount = float(amount_text)
        except ValueError:
            self.resultChanged.emit("Введите корректное число")
            return

        char_code = currency_text.split()[0]

        if char_code not in self.rates:
            self.resultChanged.emit("Курс валюты не найден")
            return

        result = amount * self.rates[char_code]
        self.resultChanged.emit(f"Результат: {result:.2f} RUB")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()
    converter = CurrencyConverter()

    engine.rootContext().setContextProperty("backend", converter)
    engine.load("main.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec_())