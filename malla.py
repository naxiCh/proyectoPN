"""Lógica de la malla decimal / sistema de punto flotante F(B, t, L, U).

Convención: x = ± 0.d1 d2 ... dt × B^e   con d1 != 0  y  L <= e <= U.
Todo se calcula con Fraction (aritmética exacta), así no aparecen errores
de float propios de Python que ensucien los resultados.

- Truncamiento (corte):  se descartan los dígitos a partir del t+1.
- Redondeo simétrico:    fl(x) = trunc(|x| + 1/2 · B^(e-t)) con el signo de x
                         (el empate se redondea "hacia afuera" del cero).
"""
from fractions import Fraction
from decimal import Decimal, localcontext
from math import floor

DIGITOS = "0123456789ABCDEF"
MAX_LARGO_ENTRADA = 500          # tope de caracteres del número a representar


class MallaError(Exception):
    """Errores propios de la malla (overflow, underflow, parámetros)."""


class OverflowMalla(MallaError):
    pass


class UnderflowMalla(MallaError):
    pass


def a_base(n: int, base: int) -> str:
    """Pasa un entero >= 0 a una cadena en la base dada."""
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, base)
        out.append(DIGITOS[r])
    return "".join(reversed(out))


def parsear(texto: str, base: int) -> Fraction:
    """Convierte un texto en base `base` (con parte fraccionaria opcional)
    a un Fraction exacto. Lanza ValueError si el texto no es válido."""
    t = texto.strip().upper().replace(",", ".")
    if not t:
        raise ValueError("Ingresá un número a representar.")
    if len(t) > MAX_LARGO_ENTRADA:
        raise ValueError(f"El número es demasiado largo (máx. {MAX_LARGO_ENTRADA} caracteres).")

    signo = 1
    if t[0] in "+-":
        signo = -1 if t[0] == "-" else 1
        t = t[1:]

    partes = t.split(".")
    if len(partes) > 2 or not "".join(partes):
        raise ValueError("El número ingresado no es válido.")

    alfabeto = DIGITOS[:base]
    for c in "".join(partes):
        if c not in alfabeto:
            raise ValueError(f"'{c}' no es un dígito válido en base {base}.")

    entera = int(partes[0] or "0", base)
    frac = Fraction(0)
    if len(partes) == 2 and partes[1]:
        frac = Fraction(int(partes[1], base), base ** len(partes[1]))
    return signo * (entera + frac)


def a_decimal_str(x: Fraction, cifras: int = 10) -> str:
    """Valor aproximado en decimal, para mostrar al usuario."""
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.Emax = 999999999
        ctx.Emin = -999999999
        d = Decimal(x.numerator) / Decimal(x.denominator)
        return f"{d:.{cifras}G}"


def fraccion_str(x: Fraction, maxlen: int = 40) -> str:
    """Valor exacto como texto, pero sin imprimir números gigantes."""
    s = str(x)
    return s if len(s) <= maxlen else "(valor exacto demasiado largo)"


class Malla:
    def __init__(self, B: int, t: int, L: int, U: int):
        if not 2 <= B <= 16:
            raise MallaError("B debe estar entre 2 y 16.")
        if t < 1:
            raise MallaError("t debe ser al menos 1.")
        if L > U:
            raise MallaError("Debe cumplirse L ≤ U.")
        self.B, self.t, self.L, self.U = B, t, L, U

    # ---------- características de la malla ----------
    def _fmt(self, mantisa_int: int, e: int, signo: str = "") -> str:
        digs = a_base(mantisa_int, self.B).rjust(self.t, "0")
        return f"{signo}0.{digs} × {self.B}^{e}"

    def menor(self) -> tuple[str, Fraction]:
        """Menor representante positivo: 0.10...0 × B^L = B^(L-1)."""
        valor = Fraction(self.B) ** (self.L - 1)
        return self._fmt(self.B ** (self.t - 1), self.L), valor

    def mayor(self) -> tuple[str, Fraction]:
        """Mayor representante: 0.(B-1)...(B-1) × B^U = (1 - B^-t) B^U."""
        valor = (1 - Fraction(self.B) ** (-self.t)) * Fraction(self.B) ** self.U
        return self._fmt(self.B ** self.t - 1, self.U), valor

    def cantidad(self) -> int:
        """2 (B-1) B^(t-1) (U-L+1) + 1   (el +1 es el cero)."""
        return 2 * (self.B - 1) * self.B ** (self.t - 1) * (self.U - self.L + 1) + 1

    def distancia(self, e: int) -> Fraction:
        """Distancia entre representantes consecutivos con exponente e: B^(e-t)."""
        return Fraction(self.B) ** (e - self.t)

    # ---------- representación de un número ----------
    def _exponente(self, a: Fraction) -> int:
        """e tal que B^(e-1) <= a < B^e   (a > 0)."""
        B = self.B
        e = 0
        if a >= 1:
            p = Fraction(1)              # p = B^e
            while a >= p:
                p *= B
                e += 1
        else:
            p = Fraction(1, B)           # p = B^(e-1)
            while a < p:
                p /= B
                e -= 1
        return e

    def representar(self, x: Fraction, modo: str) -> str:
        """modo = 'corte' (truncamiento) o 'redondeo' (simétrico)."""
        if modo not in ("corte", "redondeo"):
            raise ValueError("modo debe ser 'corte' o 'redondeo'.")
        if x == 0:
            return "0"
        signo = "-" if x < 0 else ""
        a = abs(x)
        e = self._exponente(a)

        m = a / Fraction(self.B) ** e              # mantisa en [1/B, 1)
        escala = m * self.B ** self.t              # mantisa × B^t (entero + resto)
        if modo == "corte":
            N = floor(escala)
        else:
            N = floor(escala + Fraction(1, 2))
            if N == self.B ** self.t:              # se pasó de 0.99..9 → 1.00..0
                N = self.B ** (self.t - 1)
                e += 1

        if e > self.U:
            raise OverflowMalla(f"Overflow: el exponente {e} supera U = {self.U}.")
        if e < self.L:
            raise UnderflowMalla(f"Underflow: el exponente {e} es menor que L = {self.L}.")
        return self._fmt(N, e, signo)