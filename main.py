import sys
import os
from PyQt6 import QtWidgets
import PyQt6.uic as uic
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QIntValidator
import math
from decimal import Decimal, Overflow as DecOverflow
from malla import Malla, MallaError, parsear, a_decimal_str, fraccion_str

# Importamos las funciones del módulo de lógica matemática
from logica_conversor import convertir_base
from logica_conversor import convertir_base, normalizar_pfn
from calculadora import calcular


class VentanaConversor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        ruta_ui = os.path.join(os.path.dirname(__file__), "interfaz.ui")
        uic.loadUi(ruta_ui, self)

        # Arreglo de colores: con Windows en modo oscuro, el texto de las listas
        # desplegables y de las ventanas de aviso salía blanco sobre fondo blanco.
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
        self.poblar_bases()
        self.aplicar_sombras()
        #evento malla
        self.conectar_eventos_malla()
        #evento calculadora
        self.conectar_eventos_calculadora()

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
        # 1. Obtener valores de la interfaz
        base_origen = int(self.comboBaseOrigen.currentText())
        base_destino = int(self.comboBaseDestino.currentText())
        precision_t = int(self.comboPrecision.currentText())
        texto_numero = self.txtNumero.text().strip()

        # Validar si el campo de texto está vacío
        if not texto_numero:
            self.frameAlerta.setVisible(False)
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
        self.btnMenor.clicked.connect(self.mostrar_menor)
        self.btnMayor.clicked.connect(self.mostrar_mayor)
        self.btnNumero.clicked.connect(self.mostrar_cantidad)
        self.btnDistancia.clicked.connect(self.mostrar_distancia)
        self.btnRepresentar.clicked.connect(self.representar_numero)
        self.lineRedondeo.setReadOnly(True)
        self.lineTruncamiento.setReadOnly(True)

    def leer_malla(self) -> Malla:
        """Arma la malla con los datos de la pantalla (lanza ValueError/MallaError)."""
        if self.comboB.currentIndex() < 0 or self.comboT.currentIndex() < 0:
            raise ValueError("Elegí la base B y la cantidad de dígitos t.")
        try:
            L = int(self.lineL.text())
            U = int(self.lineU.text())
        except ValueError:
            raise ValueError("Ingresá L y U como números enteros.")
        return Malla(int(self.comboB.currentText()),
                     int(self.comboT.currentText()), L, U)

    def _ejecutar_malla(self, accion):
        """Corre `accion(malla)` y muestra cualquier error en un aviso."""
        try:
            accion(self.leer_malla())
        except (ValueError, MallaError) as e:
            QtWidgets.QMessageBox.warning(self, "Labery", str(e))
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
            pfn_str = normalizar_pfn(resultado_str, base_destino)

            # Escribir en Resultado
            if hasattr(self, 'lineResultado'):
                self.lineResultado.setText(resultado_str)
            elif hasattr(self, 'txtResultado'):
                self.txtResultado.setText(resultado_str)

            # Escribir en Normalizado
            if hasattr(self, 'lineNormalizado'):
                self.lineNormalizado.setText(pfn_str)
            elif hasattr(self, 'txtNormalizado'):
                self.txtNormalizado.setText(pfn_str)

        except Exception as e:
            print("Error durante el cálculo:", e)
            self.frameAlerta.setVisible(True)

    def _info(self, titulo, texto):
        QtWidgets.QMessageBox.information(self, titulo, texto)

    def mostrar_menor(self):
        def f(m):
            txt, val = m.menor()
            self._info("Menor representante",
                       f"{txt}\n= B^(L-1) = {fraccion_str(val)}\n≈ {a_decimal_str(val)}")
        self._ejecutar_malla(f)

    def mostrar_mayor(self):
        def f(m):
            txt, val = m.mayor()
            self._info("Mayor representante",
                       f"{txt}\n= (1 - B^-t)·B^U = {fraccion_str(val)}\n≈ {a_decimal_str(val)}")
        self._ejecutar_malla(f)

    def mostrar_cantidad(self):
        def f(m):
            self._info("Números representables",
                       f"2(B-1)·B^(t-1)·(U-L+1) + 1 = {m.cantidad()}\n"
                       "(incluye el cero)")
        self._ejecutar_malla(f)

    def mostrar_distancia(self):
        def f(m):
            d_min, d_max = m.distancia(m.L), m.distancia(m.U)
            self._info("Distancia entre representantes",
                       "Entre consecutivos con exponente e la distancia es B^(e-t).\n\n"
                       f"e = L = {m.L}:  {fraccion_str(d_min)}  ≈ {a_decimal_str(d_min)}\n"
                       f"e = U = {m.U}:  {fraccion_str(d_max)}  ≈ {a_decimal_str(d_max)}")
        self._ejecutar_malla(f)

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
            if self.comboPrecisionC.currentIndex() < 0:
                raise ValueError("Elegí los dígitos de precisión.")
            if self.comboBox_2.currentIndex() < 0:
                raise ValueError("Elegí el tipo de corte.")

            x = parsear(self.lineOperando1.text(), 10)
            y = parsear(self.lineOperando2.text(), 10)
            t = int(self.comboPrecisionC.currentText())
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