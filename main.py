import sys
import os
from PyQt6 import QtWidgets
import PyQt6.uic as uic
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIntValidator
import math
from decimal import Decimal, Overflow as DecOverflow
from malla import Malla, MallaError, parsear, a_decimal_str
from cargador_pruebas import cargar_caso_prueba_txt
# Importamos las funciones del módulo de lógica matemática
from logica_conversor import convertir_base, normalizar_pfn
from calculadora import calcular
from PyQt6 import QtCore, QtWidgets, uic

from PyQt6.QtGui import QIntValidator, QValidator

class ValidadorPrecision(QIntValidator):
    def validate(self, texto: str, pos: int):
        if texto.strip() == "":
            return (QValidator.State.Intermediate, texto, pos)

        estado, texto_val, pos_val = super().validate(texto, pos)
        if estado == QValidator.State.Acceptable:
            return (QValidator.State.Acceptable, texto_val, pos_val)

        return (QValidator.State.Invalid, texto, pos)
    
class VentanaConversor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        ruta_ui = os.path.join(os.path.dirname(__file__), "interfaz.ui")
        uic.loadUi(ruta_ui, self)

        self.setStyleSheet(self.styleSheet() + """
            QComboBox QAbstractItemView { color: #22223B; background-color: #FFFFFF; }
            QComboBox QAbstractItemView::item { color: #22223B; min-height: 24px; }
            QComboBox QAbstractItemView::item:selected {
                color: #FFFFFF; background-color: #4D4566;
            }
            QMessageBox { background-color: #FFFFFF; }
            QMessageBox QLabel { color: #22223B; }
        """)

        self.frameAlerta.setVisible(False)
        self.configurar_combos_precision()       
        self.poblar_bases()
        self.aplicar_sombras()
        #evento malla
        self.conectar_eventos_malla()
        #evento calculadora
        self.conectar_eventos_calculadora()

        self.btnCalcular.clicked.connect(self.ejecutar_calculo)
        self.txtNumero.textChanged.connect(self.validar_entrada)
        self.btnCopiarResultado.clicked.connect(
            lambda _checked=False: self.copiar_a_portapapeles(self.txtResultado)
        )
        self.btnCopiarNormalizado.clicked.connect(
            lambda _checked=False: self.copiar_a_portapapeles(self.txtNormalizado)
        )

        self.comboB.setPlaceholderText("B")
        self.comboT.setPlaceholderText("t")


        self.comboB.setCurrentIndex(-1)
        self.comboT.setCurrentIndex(-1)

        validador = QIntValidator(-999, 999, self)
        self.lineL.setValidator(validador)
        self.lineU.setValidator(validador)
        if hasattr(self, "btnCargar"):
            self.btnCargar.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.btnCargar.setToolTip("Cargar caso de prueba desde archivo .txt")
            self.btnCargar.clicked.connect(lambda: cargar_caso_prueba_txt(self))

    def configurar_combos_precision(self):
        opciones_estandar = ["3", "4", "8", "12", "15", "24", "53", "64", "100"]
        validador_t = ValidadorPrecision(1, 100, self)

        for combo in self.findChildren(QtWidgets.QComboBox):
            nombre = combo.objectName().lower()
            if "precision" in nombre or combo.objectName() == "comboT":
                combo.setEditable(True)
                combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
                combo.clear()
                combo.addItems(opciones_estandar)
                combo.setCurrentText("15")
                combo.lineEdit().setValidator(validador_t)
                combo.lineEdit().setPlaceholderText("1 - 100...")
   
    def obtener_precision_valida(self, combo) -> int:
        texto = combo.currentText().strip()
        if not texto:
            raise ValueError("Ingresá un valor de precisión t (entre 1 y 100).")
        t = int(texto)
        if not (1 <= t <= 100):
            raise ValueError("La precisión t debe estar entre 1 y 100.")
        return t
    
    def poblar_bases(self):
        bases = [str(b) for b in range(2, 17)]
        self.comboBaseOrigen.clear()
        self.comboBaseDestino.clear()
        self.comboBaseOrigen.addItems(bases)
        self.comboBaseDestino.addItems(bases)
        self.comboBaseOrigen.setCurrentText("10")
        self.comboBaseDestino.setCurrentText("2")

    def aplicar_sombras(self):
        """Aplica sombras difuminadas suaves con el tono #1D3557 de la paleta."""
        elementos_con_sombra = [
            # Tarjetas laterales y alertas
            "frameAlerta", "frmAclaraciones", "frameCalculadora",
            # Botones principales
            "btnCalcular", "btnRepresentar", "btnCalcularC",
            # Botones de métricas de malla
            "btnMenor", "btnMayor", "btnNumero", "btnDistancia",
            # Botones de operaciones
            "btnSumar", "btnRestar", "btnMultiplicar", "btnDividir"
        ]

        for nombre in elementos_con_sombra:
            widget = getattr(self, nombre, None)
            if widget:
                sombra = QGraphicsDropShadowEffect(self)
                sombra.setBlurRadius(16)
                sombra.setOffset(0, 4)
                # Azul marino #1D3557 con transparencia (alpha = 45 de 255)
                sombra.setColor(QColor(29, 53, 87, 45))
                widget.setGraphicsEffect(sombra)

    def validar_entrada(self) -> bool:
        base = int(self.comboBaseOrigen.currentText())
        alfabeto = "0123456789ABCDEF"[:base]
        texto = self.txtNumero.text().strip().upper().replace(",", ".").lstrip("-")

        if not texto:
            self.frameAlerta.setVisible(False)
            return False

        partes = texto.split(".")
        if len(partes) > 2:
            self.frameAlerta.setVisible(True)
            return False

        es_valido = all(c in alfabeto for c in "".join(partes))
        self.frameAlerta.setVisible(not es_valido)
        return es_valido

    def copiar_a_portapapeles(self, campo: QtWidgets.QLineEdit) -> None:
        QtWidgets.QApplication.clipboard().setText(campo.text())

    def ejecutar_calculo(self):
        # 1. Obtener valores de la interfaz
        base_origen = int(self.comboBaseOrigen.currentText())
        base_destino = int(self.comboBaseDestino.currentText())
        texto_precision = (
            self.comboPrecision.currentText()
            if hasattr(self, "comboPrecision")
            else self.comboT.currentText()
        )
        precision_t = int(texto_precision) if texto_precision else 8
        texto_numero = self.txtNumero.text().strip()

        # Validar si el campo de texto está vacío
        if not texto_numero:
            self.frameAlerta.setVisible(False)
            return

        if not self.validar_entrada():
            return

        try:
            # 2. Realizar la conversión de base
            resultado_str = convertir_base(texto_numero, base_origen, base_destino, precision_t)
            
            # 3. Calcular el Punto Flotante Normalizado (PFN)
            pfn_str = normalizar_pfn(resultado_str, base_destino)

            # 4. Mostrar los resultados en la interfaz
            if hasattr(self, 'lineResultado'):
                self.lineResultado.setText(resultado_str)
            elif hasattr(self, 'txtResultado'):
                self.txtResultado.setText(resultado_str)

            if hasattr(self, 'lineNormalizado'):
                self.lineNormalizado.setText(pfn_str)
            elif hasattr(self, 'txtNormalizado'):
                self.txtNormalizado.setText(pfn_str)

            # Ocultar marco de alerta si el cálculo fue exitoso
            self.frameAlerta.setVisible(False)
        except Exception as e:
            print("Error durante el cálculo:", e)
            self.frameAlerta.setVisible(True)

    # ------------------------------------------------------------------
    # PESTAÑA: CÁLCULO DE MALLA
    # ------------------------------------------------------------------
    def conectar_eventos_malla(self):
        self.btnMenor.clicked.connect(self.actualizar_info_menor)
        self.btnMayor.clicked.connect(self.actualizar_info_mayor)
        self.btnNumero.clicked.connect(self.actualizar_info_cantidad)
        self.btnDistancia.clicked.connect(self.actualizar_info_distancia)
        self.btnRepresentar.clicked.connect(self.representar_numero)
        self.lineRedondeo.setReadOnly(True)
        self.lineTruncamiento.setReadOnly(True)

    def leer_malla(self) -> Malla:
        if self.comboB.currentIndex() < 0:
            raise ValueError("Elegí la base B.")
        t = self.obtener_precision_valida(self.comboT)
        try:
            L = int(self.lineL.text())
            U = int(self.lineU.text())
        except ValueError:
            raise ValueError("Ingresá L y U como números enteros.")
        return Malla(int(self.comboB.currentText()), t, L, U)
    
    def obtener_parametros_malla(self):
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
        if estimacion_exp10 < -300:
            return f"≈ 10^{estimacion_exp10:.2f} (Valor positivo infinitesimal)"

        try:
            valor = float(base) ** exponente
            return f"{valor:.6e}"
        except OverflowError:
            return f"{base}^{exponente}"

    def actualizar_info_menor(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText(
                "<b>Error de Malla</b><br><br>"
                "El exponente mínimo L debe ser menor o igual que U (L ≤ U)."
            )
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Menor Representante</b><br><br>"
                "Menor número positivo normalizado en la malla.<br><br>"
                "<i>Fórmula:</i> B<sup>-1</sup> × B<sup>L</sup> = B<sup>L-1</sup>"
            )
            return

        b, t, l, u = params
        exponente = l - 1
        valor = self.formatear_potencia_segura(b, exponente)
        self.lblAclaraciones.setText(
            f"<b>Menor Representante</b><br><br>"
            f"<b>Fórmula:</b> {b}<sup>{exponente}</sup><br><br>"
            f"<b>Valor:</b> {valor}"
        )

    def actualizar_info_mayor(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText(
                "<b>Error de Malla</b><br><br>"
                "El exponente mínimo L debe ser menor o igual que U (L ≤ U)."
            )
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Mayor Representante</b><br><br>"
                "Mayor número positivo representable en la malla.<br><br>"
                "<i>Fórmula:</i> (1 - B<sup>-t</sup>) × B<sup>U</sup>"
            )
            return

        b, t, l, u = params
        mantisa_max = 1.0 - float(b) ** (-t)
        estimacion_exp10 = u * math.log10(b)

        if estimacion_exp10 > 300:
            valor = f"{mantisa_max:.4f} × {b}<sup>{u}</sup> (Overflow en float64)"
        else:
            try:
                resultado = mantisa_max * (float(b) ** u)
                valor = f"{resultado:.6e}"
            except OverflowError:
                valor = f"{mantisa_max:.4f} × {b}<sup>{u}</sup>"

        self.lblAclaraciones.setText(
            f"<b>Mayor Representante</b><br><br>"
            f"<b>Fórmula:</b> (1 - {b}<sup>-{t}</sup>) × {b}<sup>{u}</sup><br><br>"
            f"<b>Valor:</b> {valor}"
        )

    def actualizar_info_cantidad(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText(
                "<b>Error de Malla</b><br><br>"
                "El exponente mínimo L debe ser menor o igual que U (L ≤ U)."
            )
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Números Representables</b><br><br>"
                "Cantidad total de números normalizados que contiene la malla "
                "(incluyendo el cero).<br><br>"
                "<i>Fórmula:</i> 2(B - 1) × B<sup>t-1</sup> × (U - L + 1) + 1"
            )
            return

        b, t, l, u = params
        total = 2 * (b - 1) * (b ** (t - 1)) * (u - l + 1) + 1
        total_texto = f"{total:,}"
        if len(str(total)) > 25:
            total_texto = f"≈ {total:.4e} ({len(str(total))} dígitos)"

        self.lblAclaraciones.setText(
            f"<b>Números Representables</b><br><br>"
            f"<b>Fórmula:</b> 2({b}-1) × {b}<sup>{t-1}</sup> × "
            f"({u}-({l})+1) + 1<br><br>"
            f"<b>Total en F:</b> {total_texto}"
        )

    def actualizar_info_distancia(self):
        params = self.obtener_parametros_malla()
        if params == "ERROR_RANGO":
            self.lblAclaraciones.setText(
                "<b>Error de Malla</b><br><br>"
                "El exponente mínimo L debe ser menor o igual que U (L ≤ U)."
            )
            return
        if not params:
            self.lblAclaraciones.setText(
                "<b>Distancia entre Representantes</b><br><br>"
                "Paso entre puntos consecutivos bajo un mismo exponente <i>e</i>."
                "<br><br><i>Fórmula:</i> Δ = B<sup>e - t</sup>"
            )
            return

        b, t, l, u = params
        exponente = l - t
        valor = self.formatear_potencia_segura(b, exponente)
        self.lblAclaraciones.setText(
            f"<b>Distancia entre Representantes</b><br><br>"
            f"<b>Fórmula general:</b> Δ = {b}<sup>e - {t}</sup><br><br>"
            f"<b>Paso en exponente mínimo (L={l}):</b> {valor}"
        )

    def representar_numero(self):
        # Se limpian los resultados anteriores para no mostrar datos viejos.
        for linea in (self.lineTruncamiento, self.lineRedondeo):
            linea.clear()
            linea.setToolTip("")

        # Los datos inválidos (malla o número mal escrito) se avisan en una ventana.
        try:
            m = self.leer_malla()
            x = parsear(self.lineNumero.text(), m.B)
        except (ValueError, MallaError) as e:
            QtWidgets.QMessageBox.warning(self, "Labery", str(e))
            return

        # Overflow/underflow se muestran en el propio campo (cada método por separado,
        # porque puede pasar que el truncamiento sea válido y el redondeo no).
        for linea, modo in ((self.lineTruncamiento, "corte"),
                            (self.lineRedondeo, "redondeo")):
            try:
                linea.setText(m.representar(x, modo))
                linea.setToolTip("")
            except MallaError as e:
                linea.setText(str(e).split(":")[0])   # "Overflow" / "Underflow"
                linea.setToolTip(str(e))

    #seccion calculadora
    #oyentes
    def conectar_eventos_calculadora(self):
        self.operacion = None   # acá se guarda la operación elegida

        self.comboPrecisionC.addItems([str(n) for n in range(1, 16)])
        self.comboPrecisionC.setPlaceholderText("t")
        self.comboPrecisionC.setCurrentIndex(-1)
        self.comboBox_2.setCurrentIndex(-1)

        self.grupo_ops = QtWidgets.QButtonGroup(self)
        for boton in (self.btnSumar, self.btnRestar, self.btnMultiplicar, self.btnDividir):
            boton.setCheckable(True)
            self.grupo_ops.addButton(boton)

        self.btnSumar.clicked.connect(lambda: self.elegir_operacion("+"))
        self.btnRestar.clicked.connect(lambda: self.elegir_operacion("-"))
        self.btnMultiplicar.clicked.connect(lambda: self.elegir_operacion("*"))
        self.btnDividir.clicked.connect(lambda: self.elegir_operacion("/"))

        self.btnCalcularC.clicked.connect(self.ejecutar_calculadora)

        self.lineResultadoC.setReadOnly(True)
        self.lineAbsoluto.setReadOnly(True)
        self.lineRelativo.setReadOnly(True)

    def elegir_operacion(self, op):
        self.operacion = op

    def ejecutar_calculadora(self):
        for campo in (self.lineResultadoC, self.lineAbsoluto, self.lineRelativo):
            campo.clear()

        try:
            if self.operacion is None:
                raise ValueError("Elegí una operación (+, -, *, /).")
            if self.comboBox_2.currentIndex() < 0:
                raise ValueError("Elegí el tipo de corte.")

            t = self.obtener_precision_valida(self.comboPrecisionC)
            x = parsear(self.lineOperando1.text(), 10)
            y = parsear(self.lineOperando2.text(), 10)
            modo = "corte" if self.comboBox_2.currentIndex() == 0 else "redondeo"

            r = calcular(x, y, self.operacion, t, modo)
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Labery", str(e))
            return

        self.lineResultadoC.setText(a_decimal_str(r.calculado, t))
        self.lineAbsoluto.setText(a_decimal_str(r.error_abs))
        self.lineRelativo.setText(
            a_decimal_str(r.error_rel) if r.error_rel is not None else "—")
#-----------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = VentanaConversor()
    ventana.show()
    sys.exit(app.exec())