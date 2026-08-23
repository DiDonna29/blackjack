import os
import sys
from juego import JuegoBlackJack

def habilitar_colores_consola():
    """Habilita la interpretación de secuencias ANSI en la consola de Windows si es necesario."""
    if os.name == 'nt':
        try:
            import colorama
            colorama.init(autoreset=True)
        except ImportError:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def mostrar_advertencia(mensaje: str):
    """Muestra un cuadro de advertencia visual llamativo en color rojo."""
    lineas_mensaje = [
        "⚠️  [ADVERTENCIA] ENTRADA NO VÁLIDA",
        mensaje
    ]
    # Ancho del marco basado en el mensaje
    ancho = max(len(l) for l in lineas_mensaje) + 4
    
    borde_superior = "\033[91m┌" + "─" * ancho + "┐\033[0m"
    borde_inferior = "\033[91m└" + "─" * ancho + "┘\033[0m"
    
    print(borde_superior)
    for linea in lineas_mensaje:
        espacios = ancho - len(linea)
        pad_izq = espacios // 2
        pad_der = espacios - pad_izq
        print("\033[91m│\033[0m" + " " * pad_izq + f"\033[1m\033[91m{linea}\033[0m" + " " * pad_der + "\033[91m│\033[0m")
    print(borde_inferior)
    print()

def solicitar_numero(mensaje: str, tipo=int, minimo=None, maximo=None, valor_defecto=None):
    """
    Solicita un número al usuario con reintentos automáticos y muestra
    una advertencia visual en caso de que ocurra un error de tipado o rango.
    """
    while True:
        entrada = input(mensaje).strip()
        if not entrada and valor_defecto is not None:
            return valor_defecto
            
        try:
            valor = tipo(entrada)
            if minimo is not None and valor < minimo:
                mostrar_advertencia(f"El número debe ser mayor o igual a {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                mostrar_advertencia(f"El número debe ser menor o igual a {maximo}.")
                continue
            return valor
        except ValueError:
            nombre_tipo = "entero (ej: 3)" if tipo == int else "decimal (ej: 500.50)"
            mostrar_advertencia(f"Debes ingresar un valor numérico de tipo {nombre_tipo}.")

def main():
    habilitar_colores_consola()
    
    while True:
        print("=======================================================")
        print("          ♠ ♥ ♣ ♦  CASINO BLACKJACK  ♦ ♣ ♥ ♠          ")
        print("=======================================================")
        
        # 1. Configurar número de jugadores de forma segura
        num_jugadores = solicitar_numero(
            mensaje="Ingrese el número de jugadores (1-5): ",
            tipo=int,
            minimo=1,
            maximo=5
        )
                
        # 2. Configurar nombres
        nombres = []
        for i in range(num_jugadores):
            while True:
                nombre = input(f"Nombre para el jugador #{i+1}: ").strip()
                if nombre:
                    nombres.append(nombre)
                    break
                mostrar_advertencia("El nombre del jugador no puede estar vacío.")

        # 3. Configurar número de mazos (zapato de cartas) de forma segura
        num_mazos = solicitar_numero(
            mensaje="¿Cuántos mazos en el zapato? (1-4, por defecto 1): ",
            tipo=int,
            minimo=1,
            maximo=4,
            valor_defecto=1
        )

        # 4. Configurar saldo inicial de forma segura
        saldo_inicial = solicitar_numero(
            mensaje="¿Saldo inicial por jugador? (por defecto $700): ",
            tipo=float,
            minimo=1.0,
            valor_defecto=700.0
        )

        print("\n¡Todo listo! Iniciando la mesa de juego...")
        
        # Crear el controlador e iniciar el juego
        juego = JuegoBlackJack(nombres_jugadores=nombres, saldo_inicial=saldo_inicial, num_mazos=num_mazos)
        juego.bucle_principal()
        
        # Preguntar si desea jugar de nuevo configurando una nueva mesa
        print("\n" + "=" * 55)
        reiniciar = input("¿Deseas iniciar una nueva partida configurando otra mesa? (s/n): ").strip().lower()
        if reiniciar != 's':
            print("\n¡Gracias por jugar en el Casino BlackJack! Hasta la próxima.")
            break
        print("\n" * 2)  # Separador visual antes de reiniciar

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n\033[91m\033[1m[⚠️ Juego Interrumpido] Cerrando el casino de forma segura... ¡Hasta la próxima!\033[0m")
        try:
            sys.exit(0)
        except SystemExit:
            import os
            os._exit(0)
