from fractions import Fraction
from math import floor
from dataclasses import dataclass

#def calcular(x, y, op, t, modo):
    # provisorio: solo para probar que la interfaz se conecta
 #   return f"{x} {op} {y} (t={t}, {modo})", "0", "0"

#extraido y modificado desde malla.py
def _exponente(a: Fraction, B: int = 10) -> int:
    """e tal que B^(e-1) <= a < B^e   (a > 0)."""
    e = 0
    if a >= 1:
        p = Fraction(1)
        while a >= p:
            p *= B
            e += 1
    else:
        p = Fraction(1, B)
        while a < p:
            p /= B
            e -= 1
    return e

def fl(x: Fraction, t: int, modo: str) -> Fraction:
    if modo not in ("corte", "redondeo"):
        raise ValueError("modo debe ser 'corte' o 'redondeo'.")
    if x == 0:
        return Fraction(0)
    signo = -1 if x < 0 else 1
    a = abs(x)
    e = _exponente(a)
    paso = Fraction(10) ** (e - t)            # distancia entre representantes
    escala = a / paso                         # 10^(t-1), 10^t
    N = floor(escala) if modo == "corte" else floor(escala + Fraction(1, 2))
    return signo * N * paso                   # si N llegó a 10^t, el valor sigue bien

def operar(x: Fraction, y: Fraction, op: str) -> Fraction:
    if op == "+":
        return x+y
    if op == "-":
            return x-y
    if op == "*":
            return x*y
    if op == "/":
        if y == 0:
            raise ValueError("No es posible dividir por cero")
        return x/y
    raise ValueError(f"Operacion descocnocida: {op}")        

@dataclass
class ResultadoCalculo:
    exacto: Fraction
    calculado: Fraction
    error_abs: Fraction
    error_rel: Fraction | None      # None si el exacto es 0

def calcular(x: Fraction, y: Fraction, op: str, t: int, modo: str) -> ResultadoCalculo:
    xr = fl(x, t, modo)
    yr = fl(y, t, modo)

    exacto = operar(x, y, op)

    calculado = fl(operar(xr, yr, op), t, modo)

    error_abs = abs(exacto - calculado)
    if exacto != 0:
        error_rel = error_abs / abs(exacto)
    else:
        error_rel = None

    return ResultadoCalculo(exacto, calculado, error_abs, error_rel)