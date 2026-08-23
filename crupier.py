from participante import Participante
from baraja import Baraja

class Crupier(Participante):
    def __init__(self):
        super().__init__()

    def debe_pedir(self) -> bool:
        """
        Retorna True si el crupier tiene menos de 17 puntos
        y debe pedir carta obligatoriamente según las reglas del casino.
        """
        return self.calcular_puntuacion() < 17

    def jugar_turno(self, baraja: Baraja) -> list:
        """
        Ejecuta el turno completo del crupier de forma automática.
        Pide cartas hasta alcanzar 17 puntos o más. Retorna las cartas obtenidas.
        """
        cartas_nuevas = []
        while self.debe_pedir():
            carta = baraja.repartir_carta()
            self.recibir_carta(carta)
            cartas_nuevas.append(carta)
        return cartas_nuevas

    def a_diccionario(self, ocultar_primera: bool = False) -> dict:
        """
        Serializa el estado del crupier a un diccionario.
        Útil para integraciones web (HTML/JSON).
        """
        if ocultar_primera and len(self._mano) > 0:
            mano_str = ["[Carta Oculta]"] + [str(c) for c in self._mano[1:]]
            puntuacion_visible = "Visible: " + str(self._mano[1].obtener_valor_numerico() if len(self._mano) > 1 else 0)
        else:
            mano_str = [str(c) for c in self._mano]
            puntuacion_visible = str(self.puntuacion)

        return {
            'nombre': 'Crupier',
            'mano': mano_str,
            'puntuacion_visible': puntuacion_visible,
            'puntuacion': self.puntuacion
        }
