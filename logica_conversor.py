from decimal import Decimal, getcontext
# Definimos precisión alta para los cálculos intermedios de la librería
getcontext().prec = 60

#para la conversion se va usar la base 10 como puente 
def convertir_a_base10(numero_str: str, base_origen: int) -> Decimal:
    alfabeto = "0123456789ABCDEF"
    
    # Separamos en parte entera y fraccionaria
    if "." in numero_str:
        parte_entera_str, parte_fracc_str = numero_str.upper().split(".")
    else:
        parte_entera_str, parte_fracc_str = numero_str.upper(), ""

    acumulador = Decimal('0')

    # 1 Convertir Parte Entera 
    potencia = 0
    for caracter in reversed(parte_entera_str):
        valor_digito = alfabeto.index(caracter)
        termino = Decimal(valor_digito) * (Decimal(base_origen) ** potencia)
        acumulador += termino
        potencia += 1

    # 2 Convertir Parte Fraccionaria 
    for pos, caracter in enumerate(parte_fracc_str, start=1):
        valor_digito = alfabeto.index(caracter)
        # Decimal(base_origen) ** (-pos)
        base_elevada = Decimal(base_origen) ** pos
        termino = Decimal(valor_digito) / base_elevada
        acumulador += termino

    return acumulador

def convertir_desde_base10(valor_decimal: Decimal, base_destino: int, precision_t: int = 8) -> str:
    alfabeto = "0123456789ABCDEF"
    
    # Separamos en parte entera y parte fraccionaria de Base 10
    parte_entera = int(valor_decimal)
    parte_fracc = valor_decimal - Decimal(parte_entera)

    # 1 PARTE ENTERA: Divisiones reiteradas 
    if parte_entera == 0:
        str_entera = "0"
    else:
        restos = []
        actual = parte_entera
        while actual > 0:
            resto = actual % base_destino
            restos.append(alfabeto[resto])
            actual //= base_destino
        # Invertimos la lista porque los restos se leen de abajo hacia arriba
        str_entera = "".join(reversed(restos))

    #  2 PARTE FRACCIONARIA: Multiplicaciones reiteradas
    if parte_fracc == Decimal('0'):
        str_fracc = ""
    else:
        digitos_fracc = []
        actual_fracc = parte_fracc
        contador = 0
        
        # Iteramos hasta alcanzar los t dígitos de precisión solicitados
        while actual_fracc > Decimal('0') and contador < precision_t:
            producto = actual_fracc * Decimal(base_destino)
            digito = int(producto)  # Parte entera del resultado
            digitos_fracc.append(alfabeto[digito])
            actual_fracc = producto - Decimal(digito)  # Nueva parte fraccionaria
            contador += 1
            
        str_fracc = "".join(digitos_fracc)

    # Retornamos la cadena completa
    if str_fracc:
        return f"{str_entera}.{str_fracc}"
    return str_entera

def convertir_base(numero_str: str, base_origen: int, base_destino: int, precision_t: int = 8) -> str:
    # 1: Base Origen - Base 10
    valor_base10 = convertir_a_base10(numero_str, base_origen)
    
    # 2: Base 10 - Base Destino
    resultado_str = convertir_desde_base10(valor_base10, base_destino, precision_t)   
    return resultado_str
