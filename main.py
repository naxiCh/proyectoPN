import sys
import os
from PyQt6 import QtWidgets
import PyQt6.uic as uic
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIntValidator
import math
from decimal import Decimal, Overflow as DecOverflow


class VentanaConversor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        ruta_ui = os.path.join(os.path.dirname(__file__), "interfaz.ui")
        uic.loadUi(ruta_ui, self)

        self.frameAlerta.setVisible(False)
        self.poblar_bases()
        self.aplicar_sombras()
        self.conectar_eventos_malla()

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
            (self.btnCalcular, 14, 3, 35),
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

    def ejecutar_calculo(self):
        print("Botón presionado. Calculando...")

    def conectar_eventos_malla(self):
        """Conecta los 4 botones de métricas con el panel explicativo lateral."""
        self.btnMenor.clicked.connect(self.actualizar_info_menor)
        self.btnMayor.clicked.connect(self.actualizar_info_mayor)
        self.btnNumero.clicked.connect(self.actualizar_info_cantidad)
        self.btnDistancia.clicked.connect(self.actualizar_info_distancia)

    def obtener_parametros_malla(self):
        """Lee B, t, L y U desde la interfaz validando que no estén vacíos."""
        try:
            b_str = self.comboB.currentText().strip()
            t_str = self.comboT.currentText().strip()
            l_str = self.lineL.text().strip()
            u_str = self.lineU.text().strip()

            if not (b_str and t_str and l_str and u_str):
                return None

            b = int(b_str)
            t = int(t_str)
            l = int(l_str)
            u = int(u_str)

            if l > u:
                return "ERROR_RANGO"

            return b, t, l, u
        except ValueError:
            return None

    def formatear_potencia_segura(self, base: int, exponente: int) -> str:
        estimacion_exp10 = exponente * math.log10(base) if base > 0 else 0

        if estimacion_exp10 > 300:
            return f"≈ 10^{estimacion_exp10:.2f} (Supera límite flotante standard)"
        elif estimacion_exp10 < -300:
            return f"≈ 10^{estimacion_exp10:.2f} (Valor positivo infinitesimal)"

        try:
            val = float(base) ** exponente
            return f"{val:.6e}"
        except OverflowError:
            return f"{base}^{exponente}"

    def actualizar_info_menor(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText("<b>Error de Malla</b><br><br>El exponente mínimo L debe ser menor o igual que U (L ≤ U).")
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Menor Representante</b><br><br>"
                "Menor número positivo normalizado en la malla.<br><br>"
                "<i>Fórmula:</i> B<sup>-1</sup> × B<sup>L</sup> = B<sup>L-1</sup>"
            )
            return

        b, t, l, u = params
        exp_final = l - 1
        valor_str = self.formatear_potencia_segura(b, exp_final)

        self.lblAclaraciones.setText(
            f"<b>Menor Representante</b><br><br>"
            f"<b>Fórmula:</b> {b}<sup>{exp_final}</sup><br><br>"
            f"<b>Valor:</b> {valor_str}"
        )

    def actualizar_info_mayor(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText("<b>Error de Malla</b><br><br>El exponente mínimo L debe ser menor o igual que U (L ≤ U).")
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Mayor Representante</b><br><br>"
                "Mayor número positivo representable en la malla.<br><br>"
                "<i>Fórmula:</i> (1 - B<sup>-t</sup>) × B<sup>U</sup>"
            )
            return

        b, t, l, u = params
        mantisa_max = 1.0 - (float(b) ** (-t))
        estimacion_exp10 = u * math.log10(b)

        if estimacion_exp10 > 300:
            valor_str = f"{mantisa_max:.4f} × {b}<sup>{u}</sup> (Overflow en float64)"
        else:
            try:
                val = mantisa_max * (float(b) ** u)
                valor_str = f"{val:.6e}"
            except OverflowError:
                valor_str = f"{mantisa_max:.4f} × {b}<sup>{u}</sup>"

        self.lblAclaraciones.setText(
            f"<b>Mayor Representante</b><br><br>"
            f"<b>Fórmula:</b> (1 - {b}<sup>-{t}</sup>) × {b}<sup>{u}</sup><br><br>"
            f"<b>Valor:</b> {valor_str}"
        )

    def actualizar_info_cantidad(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText("<b>Error de Malla</b><br><br>El exponente mínimo L debe ser menor o igual que U (L ≤ U).")
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Números Representables</b><br><br>"
                "Cantidad total de números normalizados que contiene la malla (incluyendo el cero).<br><br>"
                "<i>Fórmula:</i> 2(B - 1) × B<sup>t-1</sup> × (U - L + 1) + 1"
            )
            return

        b, t, l, u = params
        try:
            total = 2 * (b - 1) * (b ** (t - 1)) * (u - l + 1) + 1
            total_str = f"{total:,}"
            if len(str(total)) > 25:
                total_str = f"≈ {total:.4e} ({len(str(total))} dígitos)"
        except Exception:
            total_str = "Número demasiado grande para procesar"

        self.lblAclaraciones.setText(
            f"<b>Números Representables</b><br><br>"
            f"<b>Fórmula:</b> 2({b}-1) × {b}<sup>{t-1}</sup> × ({u}-({l})+1) + 1<br><br>"
            f"<b>Total en F:</b> {total_str}"
        )

    def actualizar_info_distancia(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText("<b>Error de Malla</b><br><br>El exponente mínimo L debe ser menor o igual que U (L ≤ U).")
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Distancia entre Representantes</b><br><br>"
                "Paso entre puntos consecutivos bajo un mismo exponente <i>e</i>.<br><br>"
                "<i>Fórmula:</i> Δ = B<sup>e - t</sup>"
            )
            return

        b, t, l, u = params
        exp_min = l - t
        valor_str = self.formatear_potencia_segura(b, exp_min)

        self.lblAclaraciones.setText(
            f"<b>Distancia entre Representantes</b><br><br>"
            f"<b>Fórmula general:</b> Δ = {b}<sup>e - {t}</sup><br><br>"
            f"<b>Paso en exponente mínimo (L={l}):</b> {valor_str}"
        )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = VentanaConversor()
    ventana.show()
    sys.exit(app.exec())