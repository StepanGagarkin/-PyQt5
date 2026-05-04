import sys
import requests
import xml.etree.ElementTree as ET

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QMessageBox
)


class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер валют в рубли")
        self.setGeometry(300, 300, 300, 200)

        self.rates = {}

        self.init_ui()
        self.load_rates()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Введите сумму:")
        layout.addWidget(self.label)

        self.amount_input = QLineEdit()
        layout.addWidget(self.amount_input)

        self.currency_box = QComboBox()
        self.currency_box.addItems([
            "USD (Доллар)",
            "EUR (Евро)",
            "JPY (Иена)",
            "CNY (Юань)",
            "GBP (Фунт стерлингов)"
        ])
        layout.addWidget(self.currency_box)

        self.convert_button = QPushButton("Перевести в рубли")
        self.convert_button.clicked.connect(self.convert_currency)
        layout.addWidget(self.convert_button)

        self.result_label = QLabel("Результат:")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

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
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки курсов:\n{e}")

    def convert_currency(self):
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректное число")
            return

        currency_text = self.currency_box.currentText()
        char_code = currency_text.split()[0]

        if char_code not in self.rates:
            QMessageBox.warning(self, "Ошибка", "Курс валюты не найден")
            return

        result = amount * self.rates[char_code]
        self.result_label.setText(f"Результат: {result:.2f} RUB")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyConverter()
    window.show()
    sys.exit(app.exec_())