

def convertir_base(numero_str: str, base_origen: int, base_destino: int, precision_t: int = 8):{
    """En java utilizamos elementos como textField, de ese elemento
    extraíamos sus valores con getText()"""
}
from decimal import Decimal, getcontext

# Definimos precisión alta para los cálculos intermedios
getcontext().prec = 60

def convertir_a_base10(numero_str: str, base_origen: int) -> Decimal:
    alfabeto = "0123456789ABCDEF"
    
    # Separamos en parte entera y fraccionaria
    if "." in numero_str:
        parte_entera_str, parte_fracc_str = numero_str.upper().split(".")
    else:
        parte_entera_str, parte_fracc_str = numero_str.upper(), ""

    acumulador = Decimal('0')

    # 1. Convertir Parte Entera (evaluación posicional)
    potencia = 0
    for caracter in reversed(parte_entera_str):
        valor_digito = alfabeto.index(caracter)
        termino = Decimal(valor_digito) * (Decimal(base_origen) ** potencia)
        acumulador += termino
        potencia += 1

    # 2. Convertir Parte Fraccionaria (potencias negativas)
    potencia = -1
    for caracter in parte_fracc_str:
        valor_digito = alfabeto.index(caracter)
        termino = Decimal(valor_digito) * (Decimal(base_origen) ** potencia)
        acumulador += termino
        potencia -= 1

    return acumulador

def convertir_desde_base10(valor_decimal: Decimal, base_destino: int, precision_t: int = 8) -> str:
    alfabeto = "0123456789ABCDEF"

    parte_entera = int(valor_decimal)
    parte_fraccionaria = valor_decimal - Decimal(parte_entera)

    # 1. Convertir Parte Entera por divisiones sucesivas
    if parte_entera == 0:
        res_entero = "0"
    else:
        digitos_enteros = []
        temp = parte_entera
        while temp > 0:
            resto = temp % base_destino
            digitos_enteros.append(alfabeto[resto])
            temp //= base_destino
        res_entero = "".join(reversed(digitos_enteros))

    # 2. Convertir Parte Fraccionaria por multiplicaciones sucesivas
    if parte_fraccionaria == Decimal('0'):
        return res_entero

    digitos_fracc = []
    temp_fracc = parte_fraccionaria
    
    for _ in range(precision_t):
        if temp_fracc == Decimal('0'):
            break
        temp_fracc *= Decimal(base_destino)
        digito = int(temp_fracc)
        digitos_fracc.append(alfabeto[digito])
        temp_fracc -= Decimal(digito)

    res_fraccionario = "".join(digitos_fracc)
    return f"{res_entero}.{res_fraccionario}" if res_fraccionario else res_entero

def convertir_base(numero_str: str, base_origen: int, base_destino: int, precision_t: int = 8) -> str:
    if base_origen == base_destino:
        return numero_str.upper()
        
    valor_base10 = convertir_a_base10(numero_str, base_origen)
    return convertir_desde_base10(valor_base10, base_destino, precision_t)

