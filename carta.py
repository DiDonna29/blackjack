class Carta:
    # Información de los palos, sus símbolos y colores correspondientes
    INFORMACION_PALOS = {
        'Corazón': {'simbolo': '♥', 'color': '\033[31m'},    # Rojo
        'Diamante': {'simbolo': '♦', 'color': '\033[31m'},   # Rojo
        'Trébol': {'simbolo': '♣', 'color': '\033[32m'},     # Verde
        'Espada': {'simbolo': '♠', 'color': '\033[34m'}      # Azul
    }
    RESETEAR_COLOR = '\033[0m'
    
    def __init__(self, palo: str, valor_nominal: str):
        if palo not in self.INFORMACION_PALOS:
            raise ValueError(f"Palo no válido: {palo}")
        self._palo = palo
        self._valor_nominal = valor_nominal

    @property
    def palo(self) -> str:
        return self._palo

    @property
    def valor_nominal(self) -> str:
        return self._valor_nominal

    def obtener_valor_numerico(self) -> int:
        """Devuelve el valor numérico base de la carta según las reglas del BlackJack."""
        if self._valor_nominal in ['J', 'Q', 'K']:
            return 10
        elif self._valor_nominal == 'A':
            return 11
        else:
            return int(self._valor_nominal)

    def obtener_representacion_ascii(self, oculta: bool = False) -> list[str]:
        """
        Retorna una lista de 5 strings que representan las líneas de la carta en ASCII.
        Si oculta es True, se muestra el reverso de la carta con las siglas 'BJ'.
        """
        if oculta:
            # Representación del reverso de la carta en color gris oscuro
            color_reverso = '\033[90m'
            return [
                f"{color_reverso}┌─────────┐{self.RESETEAR_COLOR}",
                f"{color_reverso}│░░░░░░░░░│{self.RESETEAR_COLOR}",
                f"{color_reverso}│░░ B J ░░│{self.RESETEAR_COLOR}",
                f"{color_reverso}│░░░░░░░░░│{self.RESETEAR_COLOR}",
                f"{color_reverso}└─────────┘{self.RESETEAR_COLOR}"
            ]
            
        informacion = self.INFORMACION_PALOS[self._palo]
        simbolo = informacion['simbolo']
        color = informacion['color']
        
        # Ajustamos el espaciado para el valor nominal (por ejemplo, '10' ocupa 2 caracteres)
        valor = self._valor_nominal
        if valor == '10':
            valor_superior = "10 "
            valor_inferior = " 10"
        else:
            valor_superior = f"{valor}  "
            valor_inferior = f"  {valor}"
            
        return [
            "┌─────────┐",
            f"│ {color}{valor_superior}{self.RESETEAR_COLOR}    │",
            f"│    {color}{simbolo}{self.RESETEAR_COLOR}    │",
            f"│    {color}{valor_inferior}{self.RESETEAR_COLOR} │",
            "└─────────┘"
        ]

    def __str__(self) -> str:
        return f"{self._valor_nominal} de {self._palo}"
