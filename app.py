from flask import Flask, request, jsonify, render_template_string
from carta import Carta
from baraja import Baraja
from jugador import Jugador
from crupier import Crupier
import os

app = Flask(__name__)

# Variables globales para simplificar el estado en la sesión local de un jugador
baraja_global = None
jugadores_global = []
crupier_global = None
indice_jugador_activo = 0
estado_juego = "configuracion"  # "configuracion", "apuestas", "jugando", "resultados"
mensajes_resultados = {}  # Mapea nombre de jugador a mensaje de resultado
num_mazos_config = 1
saldo_inicial_config = 700.0

@app.route('/')
def index():
    # Renderizamos la interfaz HTML responsiva y premium desde un string
    return render_template_string(HTML_INTERFAZ)

@app.route('/api/inicializar', methods=['POST'])
def api_inicializar():
    global baraja_global, jugadores_global, crupier_global, estado_juego, indice_jugador_activo, num_mazos_config, saldo_inicial_config
    
    datos = request.json or {}
    nombres = datos.get('nombres', [])
    num_mazos = int(datos.get('num_mazos', 1))
    saldo_inicial = float(datos.get('saldo_inicial', 700.0))
    
    if not nombres:
        return jsonify({'error': 'Debe haber al menos un jugador'}), 400
        
    num_mazos_config = num_mazos
    saldo_inicial_config = saldo_inicial
    
    # Instanciamos nuestras clases del dominio POO
    baraja_global = Baraja(num_mazos)
    crupier_global = Crupier()
    jugadores_global = [Jugador(nombre, saldo_inicial) for nombre in nombres]
    
    indice_jugador_activo = 0
    estado_juego = "apuestas"
    
    return jsonify(obtener_estado_diccionario())

@app.route('/api/apostar', methods=['POST'])
def api_apostar():
    global baraja_global, jugadores_global, crupier_global, estado_juego, indice_jugador_activo, mensajes_resultados
    
    if estado_juego != "apuestas":
        return jsonify({'error': 'No es fase de apuestas'}), 400
        
    datos = request.json or {}
    apuestas = datos.get('apuestas', {})  # Mapea índice de jugador a apuesta (float)
    
    jugadores_con_apuesta = 0
    mensajes_resultados = {}
    
    crupier_global.limpiar_mano()
    
    for idx, jugador in enumerate(jugadores_global):
        jugador.limpiar_mano()
        
        # Obtener apuesta de la entrada
        apuesta_val = float(apuestas.get(str(idx), 0.0))
        if apuesta_val > 0.0:
            if jugador.saldo_disponible > 0:
                jugador.realizar_apuesta(apuesta_val)
                jugadores_con_apuesta += 1
            else:
                jugador.apuesta_actual = 0.0
        else:
            # Si no apuesta, se asume que no juega esta ronda
            jugador.apuesta_actual = 0.0

    if jugadores_con_apuesta == 0:
        return jsonify({'error': 'Ningún jugador colocó una apuesta válida'}), 400

    # Repartir 2 cartas a cada participante
    for _ in range(2):
        for jugador in jugadores_global:
            if jugador.apuesta_actual > 0:
                jugador.pedir(baraja_global)
        crupier_global.recibir_carta(baraja_global.repartir_carta())

    # Determinar el primer jugador activo que debe tomar decisiones
    indice_jugador_activo = buscar_siguiente_jugador_activo(0)
    
    if indice_jugador_activo is None:
        # Caso raro donde todos tienen blackjack de entrada o similar
        finalizar_ronda()
    else:
        # Verificar si el primer jugador activo ya tiene Blackjack
        jugador = jugadores_global[indice_jugador_activo]
        if jugador.puntuacion == 21:
            avanzar_jugador()
        else:
            estado_juego = "jugando"

    return jsonify(obtener_estado_diccionario())

@app.route('/api/jugar', methods=['POST'])
def api_jugar():
    global baraja_global, jugadores_global, estado_juego, indice_jugador_activo
    
    if estado_juego != "jugando":
        return jsonify({'error': 'No es turno de los jugadores'}), 400
        
    datos = request.json or {}
    accion = datos.get('accion')  # "pedir", "plantarse", "doblar", "rendirse"
    
    jugador = jugadores_global[indice_jugador_activo]
    
    if accion == "pedir":
        jugador.pedir(baraja_global)
        if jugador.puntuacion >= 21:
            avanzar_jugador()
    elif accion == "plantarse":
        jugador.plantarse()
        avanzar_jugador()
    elif accion == "doblar":
        if jugador.doblar(baraja_global):
            avanzar_jugador()
        else:
            return jsonify({'error': 'Saldo insuficiente para doblar'}), 400
    elif accion == "rendirse":
        jugador.rendirse()
        avanzar_jugador()
    else:
        return jsonify({'error': 'Acción no válida'}), 400

    return jsonify(obtener_estado_diccionario())

@app.route('/api/reiniciar_ronda', methods=['POST'])
def api_reiniciar_ronda():
    global estado_juego, jugadores_global
    
    # Filtrar jugadores que no tienen saldo
    jugadores_global = [j for j in jugadores_global if j.saldo_disponible > 0]
    
    if not jugadores_global:
        estado_juego = "configuracion"
    else:
        estado_juego = "apuestas"
        
    return jsonify(obtener_estado_diccionario())

def buscar_siguiente_jugador_activo(inicio_indice: int):
    """Retorna el índice del siguiente jugador con apuesta y que no se haya plantado."""
    for i in range(inicio_indice, len(jugadores_global)):
        if jugadores_global[i].apuesta_actual > 0 and not jugadores_global[i].se_planto:
            return i
    return None

def avanzar_jugador():
    global indice_jugador_activo
    siguiente = buscar_siguiente_jugador_activo(indice_jugador_activo + 1)
    if siguiente is None:
        finalizar_ronda()
    else:
        indice_jugador_activo = siguiente
        # Si el siguiente jugador ya tiene 21 de entrada, avanzamos automáticamente
        if jugadores_global[indice_jugador_activo].puntuacion == 21:
            avanzar_jugador()

def finalizar_ronda():
    global estado_juego, crupier_global, baraja_global, jugadores_global, mensajes_resultados
    
    estado_juego = "resultados"
    puntos_crupier = crupier_global.puntuacion
    
    # Verificar si al menos un jugador no se pasó ni se rindió
    jugadores_activos = [j for j in jugadores_global if j.apuesta_actual > 0 and not j.se_rindio and j.puntuacion <= 21]
    
    if jugadores_activos:
        # Crupier juega automáticamente
        crupier_global.jugar_turno(baraja_global)
        puntos_crupier = crupier_global.puntuacion
        
    # Liquidar apuestas
    for jugador in jugadores_global:
        if jugador.apuesta_actual <= 0:
            continue
            
        puntos_jugador = jugador.puntuacion
        apuesta = jugador.apuesta_actual
        nombre = jugador.nombre
        
        if jugador.se_rindio:
            jugador.devolver_apuesta(0.5)
            mensajes_resultados[nombre] = f"Rendición. Pierdes ${apuesta*0.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
        elif puntos_jugador > 21:
            jugador.devolver_apuesta(0.0)
            mensajes_resultados[nombre] = f"Te pasaste (Bust). Pierdes ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
        elif puntos_crupier > 21:
            es_blackjack = (puntos_jugador == 21 and len(jugador.mano) == 2)
            factor = 2.5 if es_blackjack else 2.0
            jugador.devolver_apuesta(factor)
            if es_blackjack:
                mensajes_resultados[nombre] = f"¡BlackJack Natural! Ganas ${apuesta*1.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
            else:
                mensajes_resultados[nombre] = f"¡Ganaste! El Crupier se pasó. Ganas ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
        else:
            if puntos_jugador > puntos_crupier:
                es_blackjack = (puntos_jugador == 21 and len(jugador.mano) == 2)
                factor = 2.5 if es_blackjack else 2.0
                jugador.devolver_apuesta(factor)
                if es_blackjack:
                    mensajes_resultados[nombre] = f"¡BlackJack Natural! Ganas ${apuesta*1.5:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
                else:
                    mensajes_resultados[nombre] = f"¡Ganaste! Ganas ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
            elif puntos_jugador == puntos_crupier:
                jugador.devolver_apuesta(1.0)
                mensajes_resultados[nombre] = f"Empate (Push). Recuperas tu apuesta de ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"
            else:
                jugador.devolver_apuesta(0.0)
                mensajes_resultados[nombre] = f"Perdiste. Crupier tiene {puntos_crupier} puntos. Pierdes ${apuesta:.2f}. Saldo: ${jugador.saldo_disponible:.2f}"

def obtener_estado_diccionario():
    global jugadores_global, crupier_global, estado_juego, indice_jugador_activo, mensajes_resultados
    
    # Ocultar primera carta del crupier si estamos jugando
    ocultar_crupier = (estado_juego == "jugando" or estado_juego == "apuestas")
    
    # Para mapear los palos a símbolos gráficos visuales en la interfaz web
    crupier_dict = None
    if crupier_global:
        mano_detallada = []
        for i, carta in enumerate(crupier_global.mano):
            if i == 0 and ocultar_crupier:
                mano_detallada.append({'oculta': True})
            else:
                mano_detallada.append({
                    'oculta': False,
                    'valor': carta.valor_nominal,
                    'palo': carta.palo,
                    'simbolo': Carta.INFORMACION_PALOS[carta.palo]['simbolo'],
                    'color': 'red' if carta.palo in ['Corazón', 'Diamante'] else 'black'
                })
        crupier_dict = {
            'nombre': 'Crupier',
            'mano': mano_detallada,
            'puntuacion_visible': crupier_global.a_diccionario(ocultar_primera=ocultar_crupier)['puntuacion_visible']
        }
        
    jugadores_dict = []
    for j in jugadores_global:
        mano_detallada = []
        for carta in j.mano:
            mano_detallada.append({
                'oculta': False,
                'valor': carta.valor_nominal,
                'palo': carta.palo,
                'simbolo': Carta.INFORMACION_PALOS[carta.palo]['simbolo'],
                'color': 'red' if carta.palo in ['Corazón', 'Diamante'] else 'black'
            })
        j_dict = j.a_diccionario()
        j_dict['mano_detallada'] = mano_detallada
        jugadores_dict.append(j_dict)
        
    return {
        'estado_juego': estado_juego,
        'indice_jugador_activo': indice_jugador_activo if estado_juego == "jugando" else None,
        'crupier': crupier_dict,
        'jugadores': jugadores_dict,
        'mensajes_resultados': mensajes_resultados
    }

# =====================================================================
# INTERFAZ WEB HTML + CSS (Tailwind) + JS EMBEBIDA
# =====================================================================
HTML_INTERFAZ = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Casino BlackJack POO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: radial-gradient(circle, #106637 0%, #07351c 100%);
        }
        .carta-sombra {
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
    </style>
</head>
<body class="min-h-screen text-white font-sans">

    <!-- Encabezado Principal -->
    <header class="py-4 bg-black bg-opacity-40 border-b border-green-700 shadow-md">
        <div class="max-w-6xl mx-auto px-4 flex justify-between items-center">
            <h1 class="text-2xl md:text-3xl font-extrabold tracking-widest text-green-400">
                ♠ ♥ CASINO BLACKJACK POO ♣ ♦
            </h1>
            <span class="px-3 py-1 bg-green-900 border border-green-500 rounded text-sm text-green-300 font-mono">
                Motor Python Web
            </span>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-8">
        
        <!-- Alerta de Advertencia Visual -->
        <div id="contenedor-advertencia" class="hidden mb-6 max-w-lg mx-auto bg-red-950 border-2 border-red-500 text-red-200 px-4 py-3 rounded-lg relative shadow-xl" role="alert">
            <strong class="font-bold flex items-center">
                <span class="mr-2 text-xl">⚠️</span> [ADVERTENCIA] ENTRADA NO VÁLIDA
            </strong>
            <span id="mensaje-advertencia" class="block sm:inline mt-1">Mensaje de error</span>
        </div>

        <!-- SECCIÓN 1: CONFIGURACIÓN INICIAL -->
        <section id="sec-configuracion" class="bg-black bg-opacity-50 p-6 rounded-2xl border border-green-950 shadow-2xl max-w-xl mx-auto">
            <h2 class="text-xl font-bold mb-4 border-b border-green-900 pb-2 text-green-400">Configuración de la Mesa</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold mb-1">Número de Jugadores (1-5)</label>
                    <input id="config-num-jugadores" type="number" min="1" max="5" value="1" 
                           class="w-full bg-green-950 border border-green-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-400" />
                </div>
                
                <div id="contenedor-nombres" class="space-y-2">
                    <!-- Nombres de jugadores inyectados dinámicamente -->
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-semibold mb-1">Cantidad de Mazos (1-4)</label>
                        <input id="config-num-mazos" type="number" min="1" max="4" value="1" 
                               class="w-full bg-green-950 border border-green-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-400" />
                    </div>
                    <div>
                        <label class="block text-sm font-semibold mb-1">Saldo Inicial ($)</label>
                        <input id="config-saldo-inicial" type="number" min="1" value="700" 
                               class="w-full bg-green-950 border border-green-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-400" />
                    </div>
                </div>
                
                <button onclick="inicializarJuego()" class="w-full mt-4 bg-green-500 hover:bg-green-600 text-black font-extrabold py-3 px-6 rounded-xl transition duration-300 transform hover:scale-105 shadow-lg">
                    ABRIR MESA Y JUGAR
                </button>
            </div>
        </section>

        <!-- SECCIÓN 2: PANTALLA PRINCIPAL DEL CASINO -->
        <section id="sec-juego" class="hidden space-y-8">
            
            <!-- EL CRUPIER -->
            <div class="bg-black bg-opacity-40 p-6 rounded-2xl border border-green-900 shadow-xl max-w-3xl mx-auto">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-lg font-bold text-green-300">Crupier (La Banca)</h3>
                    <span id="crupier-puntos" class="bg-green-900 px-3 py-1 rounded-full text-xs font-bold font-mono">Puntos: 0</span>
                </div>
                <div id="crupier-cartas" class="flex flex-wrap gap-3 justify-center min-h-[144px] items-center">
                    <!-- Cartas del crupier -->
                </div>
            </div>

            <!-- BOTONES DE CONTROL DE TURNO (JUGADOR ACTIVO) -->
            <div id="controles-turno" class="hidden bg-black bg-opacity-60 p-4 rounded-xl border-2 border-green-500 shadow-2xl max-w-xl mx-auto flex flex-wrap gap-3 justify-center">
                <div class="w-full text-center mb-1 text-sm font-bold text-green-400">
                    Turno Activo: <span id="nombre-jugador-activo" class="text-white uppercase">Pedro</span>
                </div>
                <button onclick="enviarAccion('pedir')" class="bg-green-600 hover:bg-green-500 text-white font-extrabold px-6 py-3 rounded-lg shadow transition transform hover:scale-105">Pedir Carta</button>
                <button onclick="enviarAccion('plantarse')" class="bg-yellow-600 hover:bg-yellow-500 text-white font-extrabold px-6 py-3 rounded-lg shadow transition transform hover:scale-105">Plantarse</button>
                <button id="btn-doblar" onclick="enviarAccion('doblar')" class="bg-blue-600 hover:bg-blue-500 text-white font-extrabold px-6 py-3 rounded-lg shadow transition transform hover:scale-105">Doblar</button>
                <button id="btn-rendirse" onclick="enviarAccion('rendirse')" class="bg-gray-600 hover:bg-gray-500 text-white font-extrabold px-6 py-3 rounded-lg shadow transition transform hover:scale-105">Rendirse</button>
            </div>

            <!-- FASE DE APUESTAS -->
            <div id="controles-apuestas" class="hidden bg-black bg-opacity-50 p-6 rounded-2xl border border-yellow-950 shadow-xl max-w-2xl mx-auto">
                <h3 class="text-lg font-bold mb-4 text-center text-yellow-400">Coloca tu Apuesta para la Ronda</h3>
                <div id="inputs-apuestas" class="space-y-4">
                    <!-- Inputs de apuestas dinámicos por jugador -->
                </div>
                <button onclick="enviarApuestas()" class="w-full mt-6 bg-yellow-500 hover:bg-yellow-600 text-black font-extrabold py-3 px-6 rounded-xl transition duration-300 transform hover:scale-105">
                    CONFIRMAR APUESTAS E INICIAR RONDA
                </button>
            </div>

            <!-- BOTÓN DE NUEVA RONDA -->
            <div id="controles-resultados" class="hidden text-center">
                <button onclick="reiniciarRonda()" class="bg-green-500 hover:bg-green-600 text-black font-extrabold px-8 py-4 rounded-xl text-lg shadow-2xl transition duration-300 transform hover:scale-105">
                    JUGAR SIGUIENTE RONDA
                </button>
            </div>

            <!-- LISTADO DE JUGADORES EN LA MESA -->
            <div id="contenedor-jugadores" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Paneles de los jugadores -->
            </div>

        </section>

    </main>

    <footer class="py-6 bg-black bg-opacity-60 border-t border-green-950 text-center text-xs text-gray-500 mt-12">
        Casino BlackJack POO © 2026 - Localizado 100% en Español
    </footer>

    <script>
        let estadoJuego = {};

        // Escucha cambios en número de jugadores en la configuración para inyectar entradas de nombres
        document.getElementById('config-num-jugadores').addEventListener('input', actualizarInputsNombres);
        actualizarInputsNombres();

        function actualizarInputsNombres() {
            const num = parseInt(document.getElementById('config-num-jugadores').value) || 1;
            const container = document.getElementById('contenedor-nombres');
            container.innerHTML = '';
            for (let i = 0; i < num; i++) {
                container.innerHTML += `
                    <div>
                        <label class="block text-xs text-gray-400 mb-0.5">Nombre Jugador #${i+1}</label>
                        <input id="nombre-jugador-${i}" type="text" value="Jugador ${i+1}" 
                               class="w-full bg-green-950 border border-green-800 rounded px-3 py-1.5 text-white focus:outline-none focus:border-green-400 text-sm" />
                    </div>
                `;
            }
        }

        function mostrarAlerta(mensaje) {
            const alerta = document.getElementById('contenedor-advertencia');
            const mensajeEl = document.getElementById('mensaje-advertencia');
            mensajeEl.textContent = mensaje;
            alerta.classList.remove('hidden');
            // Ocultar automáticamente tras 4 segundos
            setTimeout(() => {
                alerta.classList.add('hidden');
            }, 4000);
        }

        function renderizarCarta(carta) {
            if (carta.oculta) {
                return `
                    <div class="w-24 h-36 bg-gray-800 rounded-xl border-2 border-gray-600 flex flex-col justify-center items-center text-gray-500 font-bold carta-sombra relative select-none">
                        <div class="absolute inset-1 border border-dashed border-gray-700 rounded-lg flex flex-col justify-center items-center bg-gray-900 bg-opacity-40">
                            <span class="text-xs">♠ ♥ ♣ ♦</span>
                            <span class="text-xl tracking-wider text-gray-400">B J</span>
                            <span class="text-xs">♠ ♥ ♣ ♦</span>
                        </div>
                    </div>
                `;
            }
            const colorClass = carta.color === 'red' ? 'text-red-500' : 'text-gray-200';
            return `
                <div class="w-24 h-36 bg-white text-black rounded-xl border-2 border-gray-200 flex flex-col justify-between p-2.5 carta-sombra transform hover:-translate-y-2 transition duration-300 relative select-none">
                    <div class="text-sm font-bold flex justify-between items-center ${colorClass}">
                        <span>${carta.valor}</span>
                    </div>
                    <div class="text-4xl text-center flex justify-center ${colorClass}">${carta.simbolo}</div>
                    <div class="text-sm font-bold flex justify-between items-center rotate-180 ${colorClass}">
                        <span>${carta.valor}</span>
                    </div>
                </div>
            `;
        }

        async function inicializarJuego() {
            const numJugadores = parseInt(document.getElementById('config-num-jugadores').value) || 1;
            const nombres = [];
            for (let i = 0; i < numJugadores; i++) {
                const nombreVal = document.getElementById(`nombre-jugador-${i}`).value.trim();
                if (!nombreVal) {
                    mostrarAlerta(`El nombre del Jugador #${i+1} no puede estar vacío.`);
                    return;
                }
                nombres.push(nombreVal);
            }
            
            const numMazos = parseInt(document.getElementById('config-num-mazos').value) || 1;
            if (numMazos < 1 || numMazos > 4) {
                mostrarAlerta("La cantidad de mazos debe estar entre 1 y 4.");
                return;
            }
            
            const saldoInicial = parseFloat(document.getElementById('config-saldo-inicial').value) || 0.0;
            if (saldoInicial <= 0) {
                mostrarAlerta("El saldo inicial debe ser mayor a 0.");
                return;
            }

            try {
                const response = await fetch('/api/inicializar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombres, num_mazos: numMazos, saldo_inicial: saldoInicial })
                });
                const data = await response.json();
                actualizarPantalla(data);
            } catch (error) {
                mostrarAlerta("Error al conectar con el servidor.");
            }
        }

        async function enviarApuestas() {
            const apuestas = {};
            for (let i = 0; i < estadoJuego.jugadores.length; i++) {
                const inputApuesta = document.getElementById(`apuesta-input-${i}`);
                if (inputApuesta) {
                    const val = parseFloat(inputApuesta.value) || 0.0;
                    const jugador = estadoJuego.jugadores[i];
                    if (val > jugador.saldo_disponible) {
                        mostrarAlerta(`La apuesta de ${jugador.nombre} excede su saldo disponible.`);
                        return;
                    }
                    if (val <= 0 && jugador.saldo_disponible > 0) {
                        mostrarAlerta(`El jugador ${jugador.nombre} debe apostar más de $0 para participar.`);
                        return;
                    }
                    apuestas[i] = val;
                }
            }

            try {
                const response = await fetch('/api/apostar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apuestas })
                });
                if (!response.ok) {
                    const errData = await response.json();
                    mostrarAlerta(errData.error || "Error al apostar.");
                    return;
                }
                const data = await response.json();
                actualizarPantalla(data);
            } catch (error) {
                mostrarAlerta("Error de comunicación.");
            }
        }

        async function enviarAccion(accion) {
            try {
                const response = await fetch('/api/jugar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ accion })
                });
                if (!response.ok) {
                    const errData = await response.json();
                    mostrarAlerta(errData.error || "Acción denegada.");
                    return;
                }
                const data = await response.json();
                actualizarPantalla(data);
            } catch (error) {
                mostrarAlerta("Error al ejecutar acción.");
            }
        }

        async function reiniciarRonda() {
            try {
                const response = await fetch('/api/reiniciar_ronda', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                actualizarPantalla(data);
            } catch (error) {
                mostrarAlerta("Error de reinicio.");
            }
        }

        function actualizarPantalla(data) {
            estadoJuego = data;
            
            // Alternar pantallas principales
            if (data.estado_juego === "configuracion") {
                document.getElementById('sec-configuracion').classList.remove('hidden');
                document.getElementById('sec-juego').classList.add('hidden');
                return;
            }
            
            document.getElementById('sec-configuracion').classList.add('hidden');
            document.getElementById('sec-juego').classList.remove('hidden');
            
            // 1. Renderizar Crupier
            const crupierCartasDiv = document.getElementById('crupier-cartas');
            crupierCartasDiv.innerHTML = '';
            if (data.crupier && data.crupier.mano) {
                data.crupier.mano.forEach(c => {
                    crupierCartasDiv.innerHTML += renderizarCarta(c);
                });
                document.getElementById('crupier-puntos').textContent = `Puntos: ${data.crupier.puntuacion_visible}`;
            }

            // 2. Controlar visibilidad de paneles de apuestas, turno y resultados
            document.getElementById('controles-apuestas').classList.add('hidden');
            document.getElementById('controles-turno').classList.add('hidden');
            document.getElementById('controles-resultados').classList.add('hidden');

            if (data.estado_juego === "apuestas") {
                document.getElementById('controles-apuestas').classList.remove('hidden');
                const container = document.getElementById('inputs-apuestas');
                container.innerHTML = '';
                data.jugadores.forEach((j, i) => {
                    container.innerHTML += `
                        <div class="flex items-center justify-between bg-green-950 p-3 rounded-lg border border-green-800">
                            <div>
                                <span class="font-bold text-gray-200 block">${j.nombre}</span>
                                <span class="text-xs text-green-400">Saldo: $${j.saldo_disponible.toFixed(2)}</span>
                            </div>
                            <div class="flex items-center">
                                <span class="text-sm font-bold text-yellow-500 mr-2">$</span>
                                <input id="apuesta-input-${i}" type="number" value="100" min="1" max="${j.saldo_disponible}"
                                       class="w-24 bg-green-900 border border-green-600 rounded px-2 py-1 text-center text-white focus:outline-none focus:border-yellow-400 text-sm font-bold" />
                            </div>
                        </div>
                    `;
                });
            } else if (data.estado_juego === "jugando") {
                document.getElementById('controles-turno').classList.remove('hidden');
                const jActivo = data.jugadores[data.indice_jugador_activo];
                document.getElementById('nombre-jugador-activo').textContent = jActivo.nombre;
                
                // Mostrar u ocultar botón de doblar / rendirse según cantidad de cartas
                const btnDoblar = document.getElementById('btn-doblar');
                const btnRendirse = document.getElementById('btn-rendirse');
                const tiene2Cartas = jActivo.mano.length === 2;
                
                if (tiene2Cartas && jActivo.saldo_disponible >= jActivo.apuesta_actual) {
                    btnDoblar.classList.remove('hidden');
                } else {
                    btnDoblar.classList.add('hidden');
                }
                
                if (tiene2Cartas) {
                    btnRendirse.classList.remove('hidden');
                } else {
                    btnRendirse.classList.add('hidden');
                }
            } else if (data.estado_juego === "resultados") {
                document.getElementById('controles-resultados').classList.remove('hidden');
            }

            // 3. Renderizar listado de Jugadores
            const jugadoresDiv = document.getElementById('contenedor-jugadores');
            jugadoresDiv.innerHTML = '';
            
            data.jugadores.forEach((j, i) => {
                const esActivo = (data.estado_juego === "jugando" && data.indice_jugador_activo === i);
                const colorFondo = esActivo ? 'border-2 border-green-400 bg-green-950 bg-opacity-40' : 'border border-green-950 bg-black bg-opacity-40';
                
                let htmlCartas = '';
                j.mano_detallada.forEach(c => {
                    htmlCartas += renderizarCarta(c);
                });
                
                let resultadoHtml = '';
                if (data.estado_juego === "resultados" && data.mensajes_resultados[j.nombre]) {
                    const msg = data.mensajes_resultados[j.nombre];
                    let colorMsg = 'text-yellow-400';
                    if (msg.includes("Ganaste") || msg.includes("BlackJack")) colorMsg = 'text-green-400 font-extrabold';
                    if (msg.includes("Perdiste") || msg.includes("pasaste")) colorMsg = 'text-red-400';
                    resultadoHtml = `
                        <div class="mt-4 p-2 bg-black bg-opacity-60 rounded border border-green-900 text-xs ${colorMsg}">
                            ${msg}
                        </div>
                    `;
                }

                jugadoresDiv.innerHTML += `
                    <div class="p-5 rounded-2xl shadow-xl flex flex-col justify-between ${colorFondo}">
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <div>
                                    <h4 class="font-extrabold text-lg flex items-center">
                                        ${j.nombre} 
                                        ${esActivo ? '<span class="ml-2 px-1.5 py-0.5 bg-green-500 text-black text-[10px] font-bold rounded">TURNO</span>' : ''}
                                    </h4>
                                    <span class="text-xs text-green-400">Saldo: $${j.saldo_disponible.toFixed(2)}</span>
                                </div>
                                <div class="text-right">
                                    <span class="block text-xs text-gray-400">Apuesta: $${j.apuesta_actual.toFixed(2)}</span>
                                    <span class="text-xs bg-green-900 px-2 py-0.5 rounded font-bold font-mono">Pts: ${j.puntuacion}</span>
                                </div>
                            </div>
                            <div class="flex flex-wrap gap-2 justify-center min-h-[144px] items-center border border-dashed border-green-950 p-2 rounded-xl bg-black bg-opacity-20">
                                ${j.mano.length === 0 ? '<span class="text-xs text-gray-600">Aún sin cartas</span>' : htmlCartas}
                            </div>
                        </div>
                        ${resultadoHtml}
                    </div>
                `;
            });
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # Mensaje de bienvenida
    print("*" * 60)
    print(" Iniciando Servidor Web del Casino BlackJack en Puerto 5000")
    print(" Abre tu navegador en: http://127.0.0.1:5000")
    print("*" * 60)
    app.run(debug=True, port=5000)
