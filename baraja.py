import random
from carta import Carta

class Baraja:
    PALOS = ['Corazón', 'Diamante', 'Trébol', 'Espada']
    VALORES_NOMINALES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, num_mazos: int = 1):
        if not (1 <= num_mazos <= 4):
            raise ValueError("El número de mazos (zapato) debe estar entre 1 y 4.")
        self._num_mazos = num_mazos
        self._cartas: list[Carta] = []
        self._inicializar_baraja()
        
    def _inicializar_baraja(self):
        """Construye e inicializa el zapato de cartas con el número especificado de mazos."""
        self._cartas.clear()
        for _ in range(self._num_mazos):
            for palo in self.PALOS:
                for valor in self.VALORES_NOMINALES:
                    self._cartas.append(Carta(palo, valor))
        self.barajar()

    @property
    def cantidad_cartas(self) -> int:
        """Devuelve la cantidad actual de cartas en la baraja."""
        return len(self._cartas)

    @property
    def num_mazos(self) -> int:
        return self._num_mazos

    def barajar(self):
        """Mezcla aleatoriamente las cartas restantes en la baraja."""
        random.shuffle(self._cartas)

    def repartir_carta(self) -> Carta:
        """
        Extrae y devuelve la carta superior de la baraja.
        Si queda menos del 20% de las cartas totales, la baraja se reconstruye y se mezcla automáticamente.
        """
        if not self._cartas:
            self._inicializar_baraja()
            
        carta = self._cartas.pop()
        
        # Umbral del 20% del total de cartas iniciales
        total_inicial = self._num_mazos * 52
        if len(self._cartas) < (total_inicial * 0.20):
            print("\n[Sistema: El zapato de cartas tiene pocas cartas. Reconstruyendo y barajando...] ")
            self._inicializar_baraja()
            
        return carta
