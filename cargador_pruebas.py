import os
from PyQt6 import QtWidgets


def _parsear_archivo_prueba(ruta_archivo: str) -> dict:
    """Lee un archivo .txt por secciones y devuelve un diccionario estructurado."""
    datos = {"CONVERSOR": {}, "MALLA": {}, "CALCULADORA": {}}
    seccion_actual = None

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if linea.startswith("[") and linea.endswith("]"):
                seccion_actual = linea[1:-1].strip().upper()
                continue
            if "=" in linea and seccion_actual in datos:
                clave, valor = linea.split("=", 1)
                datos[seccion_actual][clave.strip().lower()] = valor.strip()

    return datos


def cargar_caso_prueba_txt(ventana: QtWidgets.QMainWindow):
    """Abre el selector de archivos, precarga las 3 pestañas y ejecuta sus cálculos."""
    carpeta_proyecto = os.path.dirname(os.path.abspath(__file__))
    ruta_defecto = os.path.join(carpeta_proyecto, "caso_prueba.txt")
    ruta_inicial = ruta_defecto if os.path.exists(ruta_defecto) else carpeta_proyecto

    ruta_archivo, _ = QtWidgets.QFileDialog.getOpenFileName(
        ventana,
        "Seleccionar archivo de caso de prueba",
        ruta_inicial,
        "Archivos de texto (*.txt);;Todos los archivos (*)"
    )

    if not ruta_archivo:
        return

    try:
        datos = _parsear_archivo_prueba(ruta_archivo)

        # --------------------------------------------------------------
        # 1. PESTAÑA 1: CONVERSOR DE BASE
        # --------------------------------------------------------------
        conv = datos["CONVERSOR"]
        if conv:
            if "base_origen" in conv:
                ventana.comboBaseOrigen.setCurrentText(conv["base_origen"])
            if "base_destino" in conv:
                ventana.comboBaseDestino.setCurrentText(conv["base_destino"])
            if "precision" in conv and hasattr(ventana, "comboPrecision"):
                ventana.comboPrecision.setCurrentText(conv["precision"])
            if "numero" in conv:
                ventana.txtNumero.setText(conv["numero"])

            ventana.ejecutar_calculo()

        # --------------------------------------------------------------
        # 2. PESTAÑA 2: CÁLCULO DE MALLA
        # --------------------------------------------------------------
        malla = datos["MALLA"]
        if malla:
            if "b" in malla:
                ventana.comboB.setCurrentText(malla["b"])
            if "t" in malla:
                ventana.comboT.setCurrentText(malla["t"])
            if "l" in malla:
                ventana.lineL.setText(malla["l"])
            if "u" in malla:
                ventana.lineU.setText(malla["u"])
            if "numero" in malla:
                ventana.lineNumero.setText(malla["numero"])

            ventana.actualizar_info_mayor()
            ventana.representar_numero()

        # --------------------------------------------------------------
        # 3. PESTAÑA 3: CALCULADORA
        # --------------------------------------------------------------
        calc = datos["CALCULADORA"]
        if calc:
            campo_op1 = getattr(ventana, "lineOperando1", getattr(ventana, "lineOpernado1", None))
            if campo_op1 and "operando1" in calc:
                campo_op1.setText(calc["operando1"])
            if "operando2" in calc:
                ventana.lineOperando2.setText(calc["operando2"])

            combo_prec_c = getattr(ventana, "comboPrecisionC", getattr(ventana, "comboPrecision_2", None))
            if combo_prec_c and "precision" in calc:
                combo_prec_c.setCurrentText(calc["precision"])

            # Seleccionar operación (+, -, *, /)
            op = calc.get("operacion", "+")
            mapa_botones = {
                "+": getattr(ventana, "btnSumar", None),
                "-": getattr(ventana, "btnRestar", None),
                "*": getattr(ventana, "btnMultiplicar", None),
                "/": getattr(ventana, "btnDividir", None),
            }
            boton_op = mapa_botones.get(op)
            if boton_op:
                boton_op.click()
                if hasattr(ventana, "operacion"):
                    ventana.operacion = op

            # Seleccionar tipo de corte (0 = Truncamiento, 1 = Redondeo Simétrico)
            combo_corte = getattr(ventana, "comboBox_2", getattr(ventana, "comboCorte", None))
            if combo_corte and "corte" in calc:
                indice_corte = 0 if calc["corte"].lower().startswith("trunc") else 1
                combo_corte.setCurrentIndex(indice_corte)

            if hasattr(ventana, "ejecutar_calculadora"):
                ventana.ejecutar_calculadora()
            elif hasattr(ventana, "ejecutar_calculo_calculadora"):
                ventana.ejecutar_calculo_calculadora()

        QtWidgets.QMessageBox.information(
            ventana,
            "Labery - Caso de Prueba",
            f"Datos cargados correctamente desde:\n{os.path.basename(ruta_archivo)}"
        )

    except Exception as e:
        QtWidgets.QMessageBox.critical(
            ventana,
            "Error al leer archivo",
            f"No se pudo procesar el archivo de prueba:\n{e}"
        )