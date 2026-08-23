from carta import Carta

class Participante:
    def __init__(self):
        self._mano: list[Carta] = []

    @property
    def mano(self) -> list[Carta]:
        """Devuelve una copia de la mano actual (lista de objetos Carta)."""
        return list(self._mano)

    @property
    def puntuacion(self) -> int:
        """Propiedad que devuelve la puntuación optimizada de la mano actual."""
        return self.calcular_puntuacion()

    def recibir_carta(self, carta: Carta):
        """Añade una carta a la mano."""
        self._mano.append(carta)

    def limpiar_mano(self):
        """Vacía la mano actual."""
        self._mano.clear()

    def calcular_puntuacion(self) -> int:
        """
        Calcula dinámicamente la puntuación de la mano.
        El As inicialmente vale 11, pero se reduce a 1 de forma iterativa
        si la puntuación total excede 21.
        """
        puntuacion = 0
        cantidad_ases = 0

        for carta in self._mano:
            valor = carta.obtener_valor_numerico()
            if carta.valor_nominal == 'A':
                cantidad_ases += 1
            puntuacion += valor

        # Si nos pasamos de 21 y tenemos ases, restamos 10 por cada as para hacerlo valer 1
        while puntuacion > 21 and cantidad_ases > 0:
            puntuacion -= 10
            cantidad_ases -= 1

        return puntuacion

    def mostrar_mano(self, ocultar_primera: bool = False):
        """
        Dibuja en consola las cartas de la mano una al lado de la otra (en paralelo).
        Si ocultar_primera es True, se mostrará el reverso de la primera carta.
        """
        if not self._mano:
            print("[Mano vacía]")
            return

        representaciones = []
        for idx, carta in enumerate(self._mano):
            ocultar = (idx == 0 and ocultar_primera)
            representaciones.append(carta.obtener_representacion_ascii(oculta=ocultar))

        # Imprimir línea por línea para alinear las cartas horizontalmente
        for i in range(5):
            linea_completa = "  ".join(rep[i] for rep in representaciones)
            print(linea_completa)

        # Mostrar puntuación parcial/total
        if ocultar_primera:
            # Mostramos solo el valor de las cartas visibles (a partir de la segunda)
            cartas_visibles = self._mano[1:]
            puntuacion_visible = 0
            ases_visibles = 0
            for carta in cartas_visibles:
                valor = carta.obtener_valor_numerico()
                if carta.valor_nominal == 'A':
                    ases_visibles += 1
                puntuacion_visible += valor
            while puntuacion_visible > 21 and ases_visibles > 0:
                puntuacion_visible -= 10
                ases_visibles -= 1
            print(f"Puntuación visible: {puntuacion_visible} + [Carta Oculta]")
        else:
            print(f"Puntuación total: {self.puntuacion}")
