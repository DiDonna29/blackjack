import os
import time
from baraja import Baraja
from jugador import Jugador
from crupier import Crupier

class JuegoBlackJack:
    # Colores ANSI para formatear la consola
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    CYAN = '\033[96m'
    NEGRITA = '\033[1m'
    RESET = '\033[0m'

    def __init__(self, nombres_jugadores: list[str], saldo_inicial: float = 700.0, num_mazos: int = 1):
        self._baraja = Baraja(num_mazos)
        self._jugadores = [Jugador(nombre, saldo_inicial) for nombre in nombres_jugadores]
        self._crupier = Crupier()
        self._ronda_actual = 0

    def limpiar_pantalla(self):
        """Limpia la consola según el sistema operativo."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def mostrar_banner(self):
        """Imprime el banner del casino en consola."""
        print(f"{self.VERDE}{self.NEGRITA}" + "=" * 55)
        print("          ♠ ♥ ♣ ♦  CASINO BLACKJACK  ♦ ♣ ♥ ♠          ")
        print("=" * 55 + f"{self.RESET}\n")

    def mostrar_advertencia(self, mensaje: str):
        """Dibuja un marco de advertencia visual muy llamativo en color rojo."""
        lineas_mensaje = [
            "⚠️  [ADVERTENCIA] ENTRADA NO VÁLIDA",
            mensaje
        ]
        # Ancho del marco basado en el mensaje
        ancho = max(len(l) for l in lineas_mensaje) + 4
        
        borde_superior = f"{self.ROJO}┌" + "─" * ancho + f"┐{self.RESET}"
        borde_inferior = f"{self.ROJO}└" + "─" * ancho + f"┘{self.RESET}"
        
        print(borde_superior)
        for linea in lineas_mensaje:
            espacios = ancho - len(linea)
            pad_izq = espacios // 2
            pad_der = espacios - pad_izq
            print(f"{self.ROJO}│{self.RESET}" + " " * pad_izq + f"{self.NEGRITA}{self.ROJO}{linea}{self.RESET}" + " " * pad_der + f"{self.ROJO}│{self.RESET}")
        print(borde_inferior)
        print() # Línea en blanco para separar
        time.sleep(1.2)

    def solicitar_apuesta(self, jugador: Jugador) -> float | str:
        """
        Solicita la apuesta de un jugador de manera segura, controlando entradas de texto inválidas
        y mostrando advertencias visuales en rojo. Retorna el valor de la apuesta o la cadena 'salir'.
        """
        while True:
            print(f"Turno de apuesta para: {self.NEGRITA}{jugador.nombre}{self.RESET}")
            print(f"Saldo disponible: {self.VERDE}${jugador.saldo_disponible:.2f}{self.RESET}")
            entrada = input(f"Ingresa tu apuesta (o escribe 'salir' para retirarte del casino): ").strip()
            
            if entrada.lower() == 'salir':
                return 'salir'
                
            try:
                apuesta = float(entrada)
                if apuesta <= 0:
                    self.mostrar_advertencia("La apuesta debe ser un número mayor a 0.")
                    continue
                if apuesta > jugador.saldo_disponible:
                    self.mostrar_advertencia(f"Saldo insuficiente. Solo posees ${jugador.saldo_disponible:.2f}")
                    continue
                return apuesta
            except ValueError:
                self.mostrar_advertencia("Debes ingresar un número válido (ej: 150) o escribir 'salir'.")

    def iniciar_ronda(self) -> bool:
        """
        Prepara una nueva ronda de juego.
        Devuelve True si hay jugadores listos con apuestas colocadas, False si todos se retiran o quedan sin saldo.
        """
        self._ronda_actual += 1
        
        # Filtrar jugadores con dinero
        jugadores_activos = [j for j in self._jugadores if j.saldo_disponible > 0]
        if not jugadores_activos:
            print(f"\n{self.ROJO}No quedan jugadores con saldo en la mesa.{self.RESET}")
            return False

        self.limpiar_pantalla()
        self.mostrar_banner()
        print(f"{self.AMARILLO}{self.NEGRITA}--- INICIANDO RONDA #{self._ronda_actual} ---{self.RESET}\n")
        
        # Limpiar manos
        self._crupier.limpiar_mano()
        for jugador in self._jugadores:
            jugador.limpiar_mano()

        # Recolectar apuestas de manera segura
        participantes_en_ronda = 0
        for jugador in jugadores_activos:
            resultado = self.solicitar_apuesta(jugador)
            if resultado == 'salir':
                print(f"El jugador {jugador.nombre} se retira de la mesa con ${jugador.saldo_disponible:.2f}.\n")
                jugador.saldo_disponible = 0  # Se marca con saldo 0 para sacarlo del bucle de juego
            else:
                jugador.realizar_apuesta(resultado)
                print(f"¡Apuesta de {self.VERDE}${resultado:.2f}{self.RESET} confirmada!\n")
                participantes_en_ronda += 1
                time.sleep(0.5)

        if participantes_en_ronda == 0:
            return False

        # Repartir 2 cartas iniciales a jugadores que apostaron y al crupier
        print(f"\n{self.CYAN}Repartiendo cartas iniciales...{self.RESET}")
        time.sleep(1)
        
        jugadores_jugando = [j for j in self._jugadores if j.apuesta_actual > 0]
        
        for _ in range(2):
            for jugador in jugadores_jugando:
                jugador.pedir(self._baraja)
            self._crupier.recibir_carta(self._baraja.repartir_carta())

        return True

    def turno_jugadores(self):
        """Maneja el flujo interactivo de decisiones para cada jugador en la ronda."""
        jugadores_jugando = [j for j in self._jugadores if j.apuesta_actual > 0]

        for jugador in jugadores_jugando:
            self.limpiar_pantalla()
            self.mostrar_banner()
            print(f"{self.AMARILLO}{self.NEGRITA}=== Turno de {jugador.nombre.upper()} ==={self.RESET}")
            print(f"Apuesta actual: {self.VERDE}${jugador.apuesta_actual:.2f}{self.RESET} | Saldo: ${jugador.saldo_disponible:.2f}\n")
            
            # Mostrar la carta visible del Crupier
            print(f"{self.NEGRITA}Mano del Crupier (una carta oculta):{self.RESET}")
            self._crupier.mostrar_mano(ocultar_primera=True)
            print("-" * 55)

            while not jugador.se_planto:
                print(f"\n{self.NEGRITA}Tu Mano:{self.RESET}")
                jugador.mostrar_mano()
                
                puntuacion = jugador.puntuacion
                if puntuacion == 21:
                    if len(jugador.mano) == 2:
                        print(f"\n{self.VERDE}{self.NEGRITA}¡★ BLACKJACK NATURAL! ★{self.RESET}")
                    else:
                        print(f"\n{self.VERDE}¡Alcanzaste 21 puntos!{self.RESET}")
                    jugador.plantarse()
                    time.sleep(2)
                    break
                    
                if puntuacion > 21:
                    print(f"\n{self.ROJO}{self.NEGRITA}¡Te has pasado de 21! (Bust){self.RESET}")
                    time.sleep(2)
                    break

                # Evaluar opciones adicionales válidas en el primer turno (solo 2 cartas)
                puede_doblar = (len(jugador.mano) == 2 and jugador.saldo_disponible >= jugador.apuesta_actual)
                puede_rendirse = (len(jugador.mano) == 2)
                
                opciones = ["1. Pedir (Carta)", "2. Plantarse"]
                mapeo_opciones = {'1': 'pedir', '2': 'plantarse'}
                
                if puede_doblar:
                    opciones.append("3. Doblar")
                    mapeo_opciones['3'] = 'doblar'
                if puede_rendirse:
                    opciones.append("4. Rendirse")
                    mapeo_opciones['4'] = 'rendirse'
                
                print(f"\nOpciones: {', '.join(opciones)}")
                decision = input("¿Qué deseas hacer? Selecciona el número: ").strip()

                if decision not in mapeo_opciones:
                    self.mostrar_advertencia("Opción no válida. Por favor, selecciona un número de la lista.")
                    continue

                accion = mapeo_opciones[decision]
                
                if accion == 'pedir':
                    carta = jugador.pedir(self._baraja)
                    print(f"\nRecibiste: {carta}")
                    time.sleep(1.2)
                elif accion == 'plantarse':
                    jugador.plantarse()
                    print(f"\nTe plantas con {jugador.puntuacion} puntos.")
                    time.sleep(1.2)
                elif accion == 'doblar':
                    print(f"\nDoblas tu apuesta a {self.VERDE}${jugador.apuesta_actual * 2:.2f}{self.RESET}.")
                    jugador.doblar(self._baraja)
                    print(f"Tu última carta recibida es: {jugador.mano[-1]}")
                    jugador.mostrar_mano()
                    if jugador.puntuacion > 21:
                        print(f"{self.ROJO}¡Te pasaste con {jugador.puntuacion} puntos!{self.RESET}")
                    time.sleep(2.5)
                elif accion == 'rendirse':
                    print(f"\nTe rindes en esta ronda. Pierdes el 50% de tu apuesta.")
                    jugador.rendirse()
                    time.sleep(1.2)

    def turno_crupier(self):
        """El crupier juega revelando su carta oculta y pidiendo según la regla automática."""
        # Solo juega si hay jugadores que no se pasaron ni se rindieron en esta ronda
        jugadores_activos = [j for j in self._jugadores if j.apuesta_actual > 0 and not j.se_rindio and j.puntuacion <= 21]
        
        self.limpiar_pantalla()
        self.mostrar_banner()
        print(f"{self.AMARILLO}{self.NEGRITA}=== TURNO DEL CRUPIER ==={self.RESET}\n")

        print("Revelando carta oculta del crupier...")
        time.sleep(1.5)
        
        print(f"\nMano del Crupier:")
        self._crupier.mostrar_mano(ocultar_primera=False)
        time.sleep(1.5)

        if not jugadores_activos:
            print(f"\n{self.CYAN}Todos los jugadores se pasaron o se rindieron. El Crupier no necesita pedir cartas.{self.RESET}")
            time.sleep(2)
            return

        # Crupier pide mientras tenga menos de 17 puntos
        while self._crupier.debe_pedir():
            print(f"\n{self.CYAN}El Crupier pide carta (tiene {self._crupier.puntuacion} puntos)...{self.RESET}")
            time.sleep(1.5)
            cartas_nuevas = self._crupier.jugar_turno(self._baraja)
            for carta in cartas_nuevas:
                print(f"Crupier recibe: {carta}")
            
            print(f"\nMano del Crupier:")
            self._crupier.mostrar_mano(ocultar_primera=False)
            time.sleep(1.5)

        puntuacion_crupier = self._crupier.puntuacion
        if puntuacion_crupier > 21:
            print(f"\n{self.ROJO}{self.NEGRITA}¡El Crupier se ha pasado de 21!{self.RESET}")
        else:
            print(f"\nEl Crupier se planta con {puntuacion_crupier} puntos.")
        time.sleep(2)

    def determinar_ganadores(self):
        """Compara puntuaciones de los jugadores contra el crupier y liquida las apuestas."""
        self.limpiar_pantalla()
        self.mostrar_banner()
        print(f"{self.AMARILLO}{self.NEGRITA}=== RESULTADOS DE LA RONDA ==={self.RESET}\n")

        puntuacion_crupier = self._crupier.puntuacion
        print(f"Crupier finaliza con {puntuacion_crupier} puntos.")
        print("-" * 55)

        jugadores_jugando = [j for j in self._jugadores if j.apuesta_actual > 0]

        for jugador in jugadores_jugando:
            puntos = jugador.puntuacion
            apuesta = jugador.apuesta_actual
            
            print(f"\nJugador: {self.NEGRITA}{jugador.nombre}{self.RESET}")
            print(f"Mano final:")
            jugador.mostrar_mano()

            if jugador.se_rindio:
                # Recupera la mitad de la apuesta
                jugador.devolver_apuesta(0.5)
                print(f"Resultado: {self.AMARILLO}Rendición{self.RESET}. Pierdes ${apuesta*0.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
            
            elif puntos > 21:
                # Perdió todo
                jugador.devolver_apuesta(0.0)
                print(f"Resultado: {self.ROJO}Perdiste (Bust){self.RESET}. Pierdes ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
            
            elif puntuacion_crupier > 21:
                # Crupier se pasó. Jugador gana.
                es_blackjack = (puntos == 21 and len(jugador.mano) == 2)
                factor = 2.5 if es_blackjack else 2.0
                jugador.devolver_apuesta(factor)
                
                if es_blackjack:
                    print(f"Resultado: {self.VERDE}¡BLACKJACK NATURAL! (Paga 3:2){self.RESET}. Ganas ${apuesta*1.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
                else:
                    print(f"Resultado: {self.VERDE}¡Ganaste! El crupier se pasó{self.RESET}. Ganas ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
            
            else:
                # Ambos en rango válido. Comparar.
                if puntos > puntuacion_crupier:
                    # Gana jugador
                    es_blackjack = (puntos == 21 and len(jugador.mano) == 2)
                    factor = 2.5 if es_blackjack else 2.0
                    jugador.devolver_apuesta(factor)
                    
                    if es_blackjack:
                        print(f"Resultado: {self.VERDE}¡BLACKJACK NATURAL! (Paga 3:2){self.RESET}. Ganas ${apuesta*1.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
                    else:
                        print(f"Resultado: {self.VERDE}¡Ganaste!{self.RESET}. Ganas ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
                
                elif puntos == puntuacion_crupier:
                    # Empate
                    jugador.devolver_apuesta(1.0)
                    print(f"Resultado: {self.CYAN}Empate (Push){self.RESET}. Recuperas tu apuesta de ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
                
                else:
                    # Gana Crupier
                    jugador.devolver_apuesta(0.0)
                    print(f"Resultado: {self.ROJO}Perdiste{self.RESET}. Crupier tiene mayor puntuación. Pierdes ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}")
            
            time.sleep(1)

        print("\n" + "-" * 55)
        # Identificar eliminados
        for jugador in self._jugadores:
            if jugador.saldo_disponible <= 0:
                print(f"{self.ROJO}{jugador.nombre} ha quedado fuera de la mesa por falta de saldo.{self.RESET}")

        input("\nPresiona Enter para continuar...")

    def bucle_principal(self):
        """Mantiene el flujo de juego activo por rondas sucesivas."""
        while True:
            # Comprobar si hay al menos un jugador con saldo
            jugadores_activos = [j for j in self._jugadores if j.saldo_disponible > 0]
            if not jugadores_activos:
                self.limpiar_pantalla()
                self.mostrar_banner()
                print(f"{self.ROJO}{self.NEGRITA}Fin del juego: Ya no quedan jugadores con saldo en la mesa.{self.RESET}")
                print("¡Gracias por visitar el Casino BlackJack!")
                break
                
            if not self.iniciar_ronda():
                self.limpiar_pantalla()
                self.mostrar_banner()
                print("¡Gracias por jugar en el Casino BlackJack!")
                print("Retirando los fondos de la mesa...")
                break

            self.turno_jugadores()
            self.turno_crupier()
            self.determinar_ganadores()

    def a_diccionario(self) -> dict:
        """
        Serializa el estado completo del juego.
        Útil para el backend en una arquitectura HTML (JSON).
        """
        return {
            'ronda_actual': self._ronda_actual,
            'cantidad_cartas_baraja': self._baraja.cantidad_cartas,
            'crupier': self._crupier.a_diccionario(),
            'jugadores': [j.a_diccionario() for j in self._jugadores]
        }
