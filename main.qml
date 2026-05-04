import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    visible: true
    width: 300
    height: 200
    title: "Конвертер валют в рубли"

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Label {
            text: "Введите сумму:"
        }

        TextField {
            id: amountInput
            placeholderText: "Введите число"
        }

        ComboBox {
            id: currencyBox
            model: [
                "USD (Доллар)",
                "EUR (Евро)",
                "JPY (Иена)",
                "CNY (Юань)",
                "GBP (Фунт стерлингов)"
            ]
        }

        Button {
            text: "Перевести в рубли"
            onClicked: {
                backend.convert_currency(amountInput.text,
                                         currencyBox.currentText)
            }
        }

        Label {
            id: resultLabel
            text: "Результат:"
        }
    }

    Connections {
        target: backend
        function onResultChanged(result) {
            resultLabel.text = result
        }
    }
}