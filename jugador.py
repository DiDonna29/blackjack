from participante import Participante
from baraja import Baraja
from carta import Carta

class Jugador(Participante):
    def __init__(self, nombre: str, saldo_inicial: float = 700.0):
        super().__init__()
        self._nombre = nombre
        self._saldo_disponible = float(saldo_inicial)
        self._apuesta_actual = 0.0
        self._se_planto = False
        self._se_rindio = False

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def saldo_disponible(self) -> float:
        return self._saldo_disponible

    @saldo_disponible.setter
    def saldo_disponible(self, cantidad: float):
        if cantidad < 0:
            self._saldo_disponible = 0.0
        else:
            self._saldo_disponible = float(cantidad)

    @property
    def apuesta_actual(self) -> float:
        return self._apuesta_actual

    @apuesta_actual.setter
    def apuesta_actual(self, cantidad: float):
        self._apuesta_actual = float(cantidad)

    @property
    def se_planto(self) -> bool:
        return self._se_planto

    @se_planto.setter
    def se_planto(self, valor: bool):
        self._se_planto = bool(valor)

    @property
    def se_rindio(self) -> bool:
        return self._se_rindio

    @se_rindio.setter
    def se_rindio(self, valor: bool):
        self._se_rindio = bool(valor)

    def realizar_apuesta(self, cantidad: float) -> bool:
        """
        Intenta realizar una apuesta con el saldo disponible.
        Resta la cantidad del saldo y la asigna a la apuesta actual.
        Devuelve True si la apuesta fue exitosa, False en caso contrario.
        """
        if cantidad <= 0:
            print("La apuesta debe ser mayor a 0.")
            return False
        if cantidad > self._saldo_disponible:
            print(f"Saldo insuficiente. Tu saldo actual es: ${self._saldo_disponible:.2f}")
            return False
            
        self._saldo_disponible -= cantidad
        self._apuesta_actual = cantidad
        self._se_planto = False
        self._se_rindio = False
        return True

    def pedir(self, baraja: Baraja) -> Carta:
        """Pide una carta de la baraja y la añade a la mano."""
        carta = baraja.repartir_carta()
        self.recibir_carta(carta)
        return carta

    def plantarse(self):
        """El jugador se planta y termina su turno."""
        self._se_planto = True

    def doblar(self, baraja: Baraja) -> bool:
        """
        Dobla la apuesta actual si el saldo es suficiente.
        Recibe exactamente una carta más y se planta de manera obligatoria.
        Devuelve True si se pudo doblar, False de lo contrario.
        """
        if self._saldo_disponible < self._apuesta_actual:
            print("No tienes suficiente saldo para doblar la apuesta.")
            return False
            
        # Descontamos el monto adicional del saldo
        self._saldo_disponible -= self._apuesta_actual
        self._apuesta_actual *= 2
        
        # Recibe una única carta adicional
        self.pedir(baraja)
        self.plantarse()
        return True

    def rendirse(self):
        """El jugador se rinde, perdiendo la mitad de su apuesta actual."""
        self._se_rindio = True
        self.plantarse()

    def devolver_apuesta(self, factor: float):
        """
        Devuelve la apuesta al saldo multiplicada por un factor de pago.
        - factor = 1.0: Recupera la apuesta original (empate).
        - factor = 2.0: Paga 1 a 1 (ganancia neta igual a la apuesta).
        - factor = 2.5: Paga 3 a 2 (BlackJack natural).
        - factor = 0.5: Devuelve la mitad de la apuesta (rendición).
        - factor = 0.0: Pierde la apuesta.
        """
        monto_retorno = self._apuesta_actual * factor
        self._saldo_disponible += monto_retorno
        self._apuesta_actual = 0.0

    def limpiar_mano(self):
        super().limpiar_mano()
        self._apuesta_actual = 0.0
        self._se_planto = False
        self._se_rindio = False

    def a_diccionario(self) -> dict:
        """
        Serializa el estado del jugador a un diccionario.
        Útil para integraciones web (HTML/JSON).
        """
        return {
            'nombre': self._nombre,
            'saldo_disponible': self._saldo_disponible,
            'apuesta_actual': self._apuesta_actual,
            'se_planto': self._se_planto,
            'se_rindio': self._se_rindio,
            'puntuacion': self.puntuacion,
            'mano': [str(c) for c in self._mano]
        }
