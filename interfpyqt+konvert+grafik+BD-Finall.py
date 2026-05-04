import sys
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QMessageBox, QSlider,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QDateEdit, QHeaderView, QTabWidget, QCheckBox,
    QRadioButton
)
from PyQt5.QtCore import Qt, QDate, QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DB_FILE = "operations.json"
SETTINGS_FILE = "settings.json"

CURRENCY_IDS = {
    "USD": "R01235",
    "EUR": "R01239",
    "GBP": "R01035",
    "JPY": "R01820",
    "CNY": "R01375"
}


class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер валют")
        self.setGeometry(300, 300, 500, 400)

        self.rates = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_rates)

        self.init_ui()
        self.load_rates()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Конвертер ---
        self.converter_tab = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel("Введите сумму:")
        layout.addWidget(self.label)

        self.amount_input = QLineEdit()
        layout.addWidget(self.amount_input)

        self.currency_box = QComboBox()
        self.currency_box.addItems(["RUB", "USD", "EUR", "JPY", "CNY", "GBP"])
        layout.addWidget(self.currency_box)

        self.target_currency_box = QComboBox()
        self.target_currency_box.addItems(["RUB", "USD", "EUR", "JPY", "CNY", "GBP"])
        layout.addWidget(self.target_currency_box)

        self.convert_button = QPushButton("Конвертировать")
        self.convert_button.clicked.connect(self.convert_currency)
        layout.addWidget(self.convert_button)

        self.round_label = QLabel("Знаков после запятой: 2")
        layout.addWidget(self.round_label)

        self.round_slider = QSlider(Qt.Horizontal)
        self.round_slider.setMinimum(0)
        self.round_slider.setMaximum(4)
        self.round_slider.setValue(2)
        self.round_slider.valueChanged.connect(self.update_round_label)
        layout.addWidget(self.round_slider)

        self.auto_update_checkbox = QCheckBox("Автообновление")
        self.auto_update_checkbox.stateChanged.connect(self.toggle_auto_update)
        layout.addWidget(self.auto_update_checkbox)

        self.dark_theme_checkbox = QCheckBox("Тёмная тема")
        self.dark_theme_checkbox.stateChanged.connect(self.toggle_theme)
        layout.addWidget(self.dark_theme_checkbox)

        self.result_label = QLabel("Результат:")
        layout.addWidget(self.result_label)

        self.converter_tab.setLayout(layout)
        self.tabs.addTab(self.converter_tab, "Конвертер")

        # --- Журнал ---
        self.log_tab = LogPage()
        self.tabs.addTab(self.log_tab, "Журнал операций")

        # --- График ---
        self.graph_tab = GraphPage(self)
        self.tabs.addTab(self.graph_tab, "График")

        self.setLayout(main_layout)

    def toggle_theme(self):
        dark = self.dark_theme_checkbox.isChecked()
        if dark:
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: white; }
                QLineEdit, QComboBox, QTableWidget { background-color: #3c3c3c; color: white; }
                QPushButton { background-color: #444; color: white; }
                QTabBar::tab { color: black; }
            """)
        else:
            self.setStyleSheet("")
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"dark": dark}, f)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
                if data.get("dark"):
                    self.dark_theme_checkbox.setChecked(True)
                    self.toggle_theme()
        except:
            pass

    def toggle_auto_update(self):
        if self.auto_update_checkbox.isChecked():
            self.timer.start(60000)
        else:
            self.timer.stop()

    def update_round_label(self):
        self.round_label.setText(f"Знаков после запятой: {self.round_slider.value()}")

    def load_rates(self):
        try:
            response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            root = ET.fromstring(response.content)
            for valute in root.findall("Valute"):
                char = valute.find("CharCode").text
                val = float(valute.find("Value").text.replace(",", "."))
                nom = int(valute.find("Nominal").text)
                self.rates[char] = val / nom

            self.graph_tab.update_graph()
        except:
            pass

    def convert_currency(self):
        try:
            amount = float(self.amount_input.text())
        except:
            return

        src = self.currency_box.currentText()
        tgt = self.target_currency_box.currentText()

        rub = amount if src == "RUB" else amount * self.rates[src]
        res = rub if tgt == "RUB" else rub / self.rates[tgt]

        res = round(res, self.round_slider.value())
        self.result_label.setText(f"Результат: {res} {tgt}")

        self.save_operation({
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_currency": src,
            "target_currency": tgt,
            "amount": amount,
            "result": res
        })

        self.log_tab.load_operations()

    def save_operation(self, op):
        try:
            try:
                with open(DB_FILE) as f:
                    data = json.load(f)
            except:
                data = []

            data.append(op)

            with open(DB_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except:
            pass


class GraphPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        layout = QVBoxLayout()

        self.currency = QComboBox()
        self.currency.addItems(["USD", "EUR", "GBP", "JPY", "CNY"])
        layout.addWidget(self.currency)

        self.month = QRadioButton("Месяц")
        self.half = QRadioButton("Полгода")
        self.year = QRadioButton("Год")
        self.month.setChecked(True)

        h = QHBoxLayout()
        h.addWidget(self.month)
        h.addWidget(self.half)
        h.addWidget(self.year)
        layout.addLayout(h)

        btn = QPushButton("Построить")
        btn.clicked.connect(self.update_graph)
        layout.addWidget(btn)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def update_graph(self):
        currency = self.currency.currentText()
        cid = CURRENCY_IDS[currency]

        end = datetime.today()
        start = end - timedelta(days=30 if self.month.isChecked() else 180 if self.half.isChecked() else 365)

        url = f"https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={start.strftime('%d/%m/%Y')}&date_req2={end.strftime('%d/%m/%Y')}&VAL_NM_RQ={cid}"

        try:
            root = ET.fromstring(requests.get(url).content)

            dates, values = [], []
            for r in root.findall("Record"):
                dates.append(datetime.strptime(r.attrib["Date"], "%d.%m.%Y"))
                values.append(float(r.find("Value").text.replace(",", ".")))

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(dates, values)
            ax.tick_params(axis='x', labelsize=6, rotation=45)
            self.figure.tight_layout()
            self.canvas.draw()
        except:
            pass


# --- ПОЛНЫЙ ЖУРНАЛ ---
class LogPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_operations()

    def init_ui(self):
        main_layout = QVBoxLayout()

        filter_layout = QHBoxLayout()

        self.date_from_input = QDateEdit(calendarPopup=True)
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_from_input)

        self.date_to_input = QDateEdit(calendarPopup=True)
        self.date_to_input.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to_input)

        self.source_currency_filter = QComboBox()
        self.source_currency_filter.addItem("Все исходные")
        self.source_currency_filter.addItems(["RUB", "USD", "EUR", "JPY", "CNY", "GBP"])
        filter_layout.addWidget(self.source_currency_filter)

        self.target_currency_filter = QComboBox()
        self.target_currency_filter.addItem("Все целевые")
        self.target_currency_filter.addItems(["RUB", "USD", "EUR", "JPY", "CNY", "GBP"])
        filter_layout.addWidget(self.target_currency_filter)

        self.amount_min_input = QLineEdit()
        self.amount_min_input.setPlaceholderText("Сумма min")
        filter_layout.addWidget(self.amount_min_input)

        self.amount_max_input = QLineEdit()
        self.amount_max_input.setPlaceholderText("Сумма max")
        filter_layout.addWidget(self.amount_max_input)

        main_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Дата", "Откуда", "Куда", "Сумма", "Результат", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        refresh = QPushButton("Обновить")
        refresh.clicked.connect(self.load_operations)
        btn_layout.addWidget(refresh)

        apply_btn = QPushButton("Фильтр")
        apply_btn.clicked.connect(self.apply_filters)
        btn_layout.addWidget(apply_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_operations(self):
        try:
            with open(DB_FILE) as f:
                self.data = json.load(f)
        except:
            self.data = []

        self.display(self.data)

    def display(self, data):
        self.table.setRowCount(len(data))
        for i, op in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(op["datetime"]))
            self.table.setItem(i, 1, QTableWidgetItem(op["source_currency"]))
            self.table.setItem(i, 2, QTableWidgetItem(op["target_currency"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(op["amount"])))
            self.table.setItem(i, 4, QTableWidgetItem(str(op["result"])))

            btn = QPushButton("Удалить")
            btn.clicked.connect(lambda _, r=i: self.delete(r))
            self.table.setCellWidget(i, 5, btn)

    def delete(self, row):
        self.data.pop(row)
        with open(DB_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
        self.load_operations()

    def apply_filters(self):
        data = self.data

        df = self.date_from_input.date().toString("yyyy-MM-dd")
        dt = self.date_to_input.date().toString("yyyy-MM-dd")

        data = [x for x in data if df <= x["datetime"][:10] <= dt]

        sc = self.source_currency_filter.currentText()
        tc = self.target_currency_filter.currentText()

        if sc != "Все исходные":
            data = [x for x in data if x["source_currency"] == sc]
        if tc != "Все целевые":
            data = [x for x in data if x["target_currency"] == tc]

        if self.amount_min_input.text():
            data = [x for x in data if float(x["amount"]) >= float(self.amount_min_input.text())]
        if self.amount_max_input.text():
            data = [x for x in data if float(x["amount"]) <= float(self.amount_max_input.text())]

        self.display(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyConverter()
    window.show()
    sys.exit(app.exec_())