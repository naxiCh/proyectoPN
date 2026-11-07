import sys
import os
from PyQt6 import QtWidgets
import PyQt6.uic as uic
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIntValidator
import math
from decimal import Decimal, Overflow as DecOverflow

# Importamos las funciones del módulo de lógica matemática
from logica_conversor import convertir_base


class VentanaConversor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        ruta_ui = os.path.join(os.path.dirname(__file__), "interfaz.ui")
        uic.loadUi(ruta_ui, self)

        self.frameAlerta.setVisible(False)
        self.poblar_bases()
        self.aplicar_sombras()
        """self.conectar_eventos_malla()"""

        self.btnCalcular.clicked.connect(self.ejecutar_calculo)
        self.txtNumero.textChanged.connect(self.validar_entrada)

        self.comboB.setPlaceholderText("B")
        self.comboT.setPlaceholderText("t")

        self.comboB.setCurrentIndex(-1)
        self.comboT.setCurrentIndex(-1)

        validador = QIntValidator(-999, 999, self)
        self.lineL.setValidator(validador)
        self.lineU.setValidator(validador)

    def poblar_bases(self):
        bases = [str(b) for b in range(2, 17)]
        self.comboBaseOrigen.clear()
        self.comboBaseDestino.clear()
        self.comboBaseOrigen.addItems(bases)
        self.comboBaseDestino.addItems(bases)
        self.comboBaseOrigen.setCurrentText("10")
        self.comboBaseDestino.setCurrentText("2")

    def aplicar_sombras(self):
       elementos = [
            (self.frameAlerta, 16, 4, 30),
            (self.txtNumero, 12, 2, 25),
        ]
       for widget, radio, dy, alpha in elementos:
            sombra = QGraphicsDropShadowEffect(widget)
            sombra.setBlurRadius(radio)
            sombra.setOffset(0, dy)
            sombra.setColor(QColor(0, 0, 0, alpha))
            widget.setGraphicsEffect(sombra)

    def validar_entrada(self):
        base = int(self.comboBaseOrigen.currentText())
        alfabeto = "0123456789ABCDEF"[:base]
        texto = self.txtNumero.text().strip().upper().replace(",", ".").lstrip("-")

        if not texto:
            self.frameAlerta.setVisible(False)
            return

        partes = texto.split(".")
        if len(partes) > 2:
            self.frameAlerta.setVisible(True)
            return

        es_valido = all(c in alfabeto for c in "".join(partes))
        self.frameAlerta.setVisible(not es_valido)
    " se agrego esto para conectar la interfaz con la logica del problema"
    def ejecutar_calculo(self):
        self.frameAlerta.setVisible(False)

        texto_numero = self.txtNumero.text().strip()
        str_origen = self.comboBaseOrigen.currentText()
        str_destino = self.comboBaseDestino.currentText()
        str_t = self.comboT.currentText()

        if not texto_numero:
            self.frameAlerta.setVisible(True)
            return

        base_origen = int(str_origen)
        base_destino = int(str_destino)
        precision_t = int(str_t) if str_t else 8

        if not (2 <= base_origen <= 16 and 2 <= base_destino <= 16):
            self.frameAlerta.setVisible(True)
            return

        try:
            resultado_str = convertir_base(texto_numero, base_origen, base_destino, precision_t)
            
            # Escribir en la casilla de resultado de PyQt6
            if hasattr(self, 'lineResultado'):
                self.lineResultado.setText(resultado_str)
            elif hasattr(self, 'txtResultado'):
                self.txtResultado.setText(resultado_str)

        except Exception as e:
            print("Error durante la conversión:", e)
            self.frameAlerta.setVisible(True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = VentanaConversor()
    ventana.show()
    sys.exit(app.exec())

""" de mi interes de aqui naim puso botenes y alerta para los numero de [2,16]
se hizo una validacion visual  en tiempo real"""
