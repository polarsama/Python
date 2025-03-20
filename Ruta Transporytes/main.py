# Sistema de Rutas para Transporte Masivo basado en Reglas Lógicas
# Este código implementa un sistema que encuentra la mejor ruta entre un punto A y B
# en un sistema de transporte masivo utilizando reglas lógicas y algoritmos de búsqueda

import heapq
import datetime
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, Optional

# Definición de estructuras de datos
@dataclass
class Estacion:
    id: str
    nombre: str
    coordenadas: Tuple[float, float]  # (latitud, longitud)
    lineas: List[str]                 # Lista de líneas que pasan por esta estación
    servicios: List[str]              # Servicios disponibles (baños, accesibilidad, etc.)
    
@dataclass
class Conexion:
    origen: str                       # ID de estación origen
    destino: str                      # ID de estación destino
    linea: str                        # Línea de transporte
    tiempo_promedio: int              # Tiempo en minutos
    distancia: float                  # Distancia en kilómetros
    activa: bool = True               # Indica si la conexión está activa
    horario: Optional[Dict] = None    # Horarios de operación por día de la semana

@dataclass
class Horario:
    hora_inicio: datetime.time
    hora_fin: datetime.time
    frecuencia: int                   # Frecuencia en minutos

@dataclass
class Ruta:
    estaciones: List[str]             # Lista de IDs de estaciones
    conexiones: List[str]             # Lista de IDs de conexiones
    tiempo_total: int                 # Tiempo total en minutos
    distancia_total: float            # Distancia total en kilómetros
    transbordos: int                  # Número de transbordos
    costo: float                      # Costo total del viaje

@dataclass
class Preferencia:
    nombre: str
    peso: float                       # Peso entre 0 y 1
    
class BaseConocimiento:
    """Clase que gestiona la base de conocimiento del sistema"""
    
    def __init__(self, archivo_reglas=None):
        self.estaciones: Dict[str, Estacion] = {}
        self.conexiones: Dict[str, Conexion] = {}
        self.reglas_logicas = []
        self.preferencias_default = [
            Preferencia("tiempo", 0.5),
            Preferencia("transbordos", 0.3),
            Preferencia("distancia", 0.1),
            Preferencia("costo", 0.1)
        ]
        
        if archivo_reglas:
            self.cargar_reglas(archivo_reglas)
            
    def cargar_reglas(self, archivo):
        """Carga las reglas lógicas desde un archivo JSON"""
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                
                # Cargar estaciones
                for estacion_data in datos.get("estaciones", []):
                    estacion = Estacion(
                        id=estacion_data["id"],
                        nombre=estacion_data["nombre"],
                        coordenadas=(estacion_data["latitud"], estacion_data["longitud"]),
                        lineas=estacion_data["lineas"],
                        servicios=estacion_data.get("servicios", [])
                    )
                    self.estaciones[estacion.id] = estacion
                
                # Cargar conexiones
                for conexion_data in datos.get("conexiones", []):
                    conexion = Conexion(
                        origen=conexion_data["origen"],
                        destino=conexion_data["destino"],
                        linea=conexion_data["linea"],
                        tiempo_promedio=conexion_data["tiempo"],
                        distancia=conexion_data["distancia"],
                        activa=conexion_data.get("activa", True),
                        horario=conexion_data.get("horario")
                    )
                    conexion_id = f"{conexion.origen}-{conexion.destino}-{conexion.linea}"
                    self.conexiones[conexion_id] = conexion
                
                # Cargar reglas lógicas
                self.reglas_logicas = datos.get("reglas", [])
                
        except Exception as e:
            print(f"Error al cargar las reglas: {e}")
    
    def aplicar_reglas(self, origen, destino, hora_actual=None, preferencias=None):
        """Aplica las reglas lógicas para modificar la red antes de la búsqueda"""
        
        # Si no se proporciona hora, usar la hora actual
        if hora_actual is None:
            hora_actual = datetime.datetime.now()
        
        # Aplicar reglas de horario
        for conexion_id, conexion in list(self.conexiones.items()):
            if not conexion.activa:
                continue
                
            # Verificar si la conexión tiene horario específico
            if conexion.horario:
                dia_semana = hora_actual.strftime("%A").lower()
                if dia_semana in conexion.horario:
                    horario_dia = conexion.horario[dia_semana]
                    hora_inicio = datetime.time(horario_dia["inicio"][0], horario_dia["inicio"][1])
                    hora_fin = datetime.time(horario_dia["fin"][0], horario_dia["fin"][1])
                    
                    # Si estamos fuera del horario, desactivar temporalmente la conexión
                    if hora_actual.time() < hora_inicio or hora_actual.time() > hora_fin:
                        conexion.activa = False
        
        # Aplicar reglas lógicas específicas
        for regla in self.reglas_logicas:
            tipo_regla = regla.get("tipo")
            
            if tipo_regla == "cierre_estacion":
                estacion_id = regla.get("estacion_id")
                if estacion_id in self.estaciones:
                    # Desactivar todas las conexiones que involucren esta estación
                    for conexion_id, conexion in self.conexiones.items():
                        if conexion.origen == estacion_id or conexion.destino == estacion_id:
                            conexion.activa = False
            
            elif tipo_regla == "cierre_linea":
                linea = regla.get("linea")
                # Desactivar todas las conexiones de esta línea
                for conexion_id, conexion in self.conexiones.items():
                    if conexion.linea == linea:
                        conexion.activa = False
            
            elif tipo_regla == "mantenimiento_tramo":
                tramo_origen = regla.get("origen")
                tramo_destino = regla.get("destino")
                for conexion_id, conexion in self.conexiones.items():
                    if (conexion.origen == tramo_origen and conexion.destino == tramo_destino) or \
                       (conexion.origen == tramo_destino and conexion.destino == tramo_origen):
                        conexion.activa = False
            
            elif tipo_regla == "congestion":
                linea = regla.get("linea")
                factor = regla.get("factor", 1.5)
                for conexion_id, conexion in self.conexiones.items():
                    if conexion.linea == linea:
                        # Aumentar el tiempo de viaje debido a la congestión
                        conexion.tiempo_promedio = int(conexion.tiempo_promedio * factor)

class SistemaRutas:
    """Clase principal del sistema de rutas"""
    
    def __init__(self, base_conocimiento):
        self.base_conocimiento = base_conocimiento
    
    def calcular_ruta(self, origen_id, destino_id, hora=None, preferencias=None):
        """
        Calcula la mejor ruta entre dos estaciones
        
        Args:
            origen_id: ID de la estación de origen
            destino_id: ID de la estación de destino
            hora: Hora de salida (datetime)
            preferencias: Lista de preferencias del usuario
            
        Returns:
            Mejor ruta encontrada
        """
        # Aplicar reglas lógicas para actualizar el estado del sistema
        self.base_conocimiento.aplicar_reglas(origen_id, destino_id, hora, preferencias)
        
        # Si no hay preferencias específicas, usar las predeterminadas
        if preferencias is None:
            preferencias = self.base_conocimiento.preferencias_default
        
        # Implementar algoritmo A* para encontrar la mejor ruta
        return self._buscar_ruta_astar(origen_id, destino_id, preferencias)
    
    def _buscar_ruta_astar(self, origen_id, destino_id, preferencias):
        """Implementa el algoritmo A* para encontrar la mejor ruta"""
        
        # Validar que las estaciones existan
        if origen_id not in self.base_conocimiento.estaciones:
            raise ValueError(f"La estación de origen {origen_id} no existe")
        if destino_id not in self.base_conocimiento.estaciones:
            raise ValueError(f"La estación de destino {destino_id} no existe")
            
        # Obtener coordenadas de destino para la heurística
        destino = self.base_conocimiento.estaciones[destino_id]
        destino_coords = destino.coordenadas
        
        # Inicialización de estructuras para A*
        cola_prioridad = []  # Cola de prioridad (heap)
        visitados = set()    # Conjunto de nodos visitados
        
        # Estructura para rastrear el camino y acumular métricas
        padres = {}  # Para reconstruir el camino
        lineas_actuales = {}  # Para rastrear la línea actual y detectar transbordos
        metricas = {
            # Para cada estación guardamos: (tiempo, distancia, transbordos, costo)
            origen_id: (0, 0, 0, 0)
        }
        
        # Agregar nodo inicial a la cola de prioridad
        # (prioridad, estación, línea_actual)
        heapq.heappush(cola_prioridad, (0, origen_id, None))
        
        while cola_prioridad:
            # Obtener el nodo con menor prioridad
            _, estacion_actual_id, linea_actual = heapq.heappop(cola_prioridad)
            
            # Si ya visitamos esta estación, continuar
            if estacion_actual_id in visitados:
                continue
                
            # Marcar como visitado
            visitados.add(estacion_actual_id)
            
            # Si llegamos al destino, reconstruir y devolver la ruta
            if estacion_actual_id == destino_id:
                return self._reconstruir_ruta(padres, origen_id, destino_id, metricas)
            
            # Explorar conexiones desde la estación actual
            for conexion_id, conexion in self.base_conocimiento.conexiones.items():
                if not conexion.activa:
                    continue
                    
                if conexion.origen == estacion_actual_id:
                    estacion_siguiente_id = conexion.destino
                    
                    # Si ya visitamos esta estación, continuar
                    if estacion_siguiente_id in visitados:
                        continue
                    
                    # Calcular métricas para esta conexión
                    tiempo_actual, distancia_actual, transbordos_actual, costo_actual = metricas[estacion_actual_id]
                    
                    # Tiempo adicional
                    tiempo_adicional = conexion.tiempo_promedio
                    
                    # Distancia adicional
                    distancia_adicional = conexion.distancia
                    
                    # Transbordos: incrementar si cambiamos de línea
                    transbordos_adicional = 0
                    if linea_actual is not None and linea_actual != conexion.linea:
                        transbordos_adicional = 1
                        # Agregar penalización de tiempo por transbordo (5 minutos)
                        tiempo_adicional += 5
                    
                    # Costo adicional (ejemplo simple: 10 unidades por conexión)
                    costo_adicional = 10
                    
                    # Actualizar métricas acumuladas
                    tiempo_nuevo = tiempo_actual + tiempo_adicional
                    distancia_nueva = distancia_actual + distancia_adicional
                    transbordos_nuevos = transbordos_actual + transbordos_adicional
                    costo_nuevo = costo_actual + costo_adicional
                    
                    # Si es una mejor ruta o no hemos visitado esta estación
                    if estacion_siguiente_id not in metricas or self._es_mejor_ruta(
                            (tiempo_nuevo, distancia_nueva, transbordos_nuevos, costo_nuevo),
                            metricas.get(estacion_siguiente_id, (float('inf'), float('inf'), float('inf'), float('inf'))),
                            preferencias):
                        
                        # Actualizar métricas
                        metricas[estacion_siguiente_id] = (tiempo_nuevo, distancia_nueva, transbordos_nuevos, costo_nuevo)
                        
                        # Actualizar padre para reconstruir ruta
                        padres[estacion_siguiente_id] = (estacion_actual_id, conexion_id)
                        
                        # Actualizar línea actual
                        lineas_actuales[estacion_siguiente_id] = conexion.linea
                        
                        # Calcular heurística (distancia directa al destino)
                        estacion_siguiente = self.base_conocimiento.estaciones[estacion_siguiente_id]
                        heuristica = self._calcular_distancia(estacion_siguiente.coordenadas, destino_coords)
                        
                        # Calcular prioridad combinando métricas actuales y heurística
                        prioridad = self._calcular_prioridad(
                            (tiempo_nuevo, distancia_nueva, transbordos_nuevos, costo_nuevo),
                            heuristica,
                            preferencias
                        )
                        
                        # Agregar a la cola de prioridad
                        heapq.heappush(cola_prioridad, (prioridad, estacion_siguiente_id, conexion.linea))
        
        # Si no se encontró ruta
        return None
    
    def _es_mejor_ruta(self, metricas_nueva, metricas_actual, preferencias):
        """Determina si una ruta es mejor que otra según las preferencias"""
        # Desempaquetar métricas
        tiempo_nuevo, distancia_nueva, transbordos_nuevos, costo_nuevo = metricas_nueva
        tiempo_actual, distancia_actual, transbordos_actual, costo_actual = metricas_actual
        
        # Normalizar y ponderar según preferencias
        valor_nuevo = 0
        valor_actual = 0
        
        for pref in preferencias:
            if pref.nombre == "tiempo":
                valor_nuevo += pref.peso * tiempo_nuevo
                valor_actual += pref.peso * tiempo_actual
            elif pref.nombre == "distancia":
                valor_nuevo += pref.peso * distancia_nueva
                valor_actual += pref.peso * distancia_actual
            elif pref.nombre == "transbordos":
                valor_nuevo += pref.peso * transbordos_nuevos * 10  # Multiplicamos para dar más peso
                valor_actual += pref.peso * transbordos_actual * 10
            elif pref.nombre == "costo":
                valor_nuevo += pref.peso * costo_nuevo
                valor_actual += pref.peso * costo_actual
        
        # Menor valor es mejor
        return valor_nuevo < valor_actual
    
    def _calcular_prioridad(self, metricas, heuristica, preferencias):
        """Calcula la prioridad para A* combinando métricas actuales y heurística"""
        tiempo, distancia, transbordos, costo = metricas
        
        # Normalizar y ponderar según preferencias
        valor = 0
        
        for pref in preferencias:
            if pref.nombre == "tiempo":
                valor += pref.peso * tiempo
            elif pref.nombre == "distancia":
                valor += pref.peso * distancia
            elif pref.nombre == "transbordos":
                valor += pref.peso * transbordos * 10  # Multiplicamos para dar más peso
            elif pref.nombre == "costo":
                valor += pref.peso * costo
        
        # Sumar heurística (distancia directa al destino)
        # Usando un factor para convertir distancia a una unidad comparable
        factor_heuristica = 2  # Ajustar según sea necesario
        return valor + heuristica * factor_heuristica
    
    def _calcular_distancia(self, coord1, coord2):
        """Calcula la distancia euclidiana entre dos coordenadas"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
    
    def _reconstruir_ruta(self, padres, origen_id, destino_id, metricas):
        """Reconstruye la ruta completa a partir de los nodos padre"""
        estaciones = []
        conexiones = []
        
        estacion_actual = destino_id
        
        # Reconstruir el camino desde el destino hasta el origen
        while estacion_actual != origen_id:
            estaciones.append(estacion_actual)
            estacion_anterior, conexion_id = padres[estacion_actual]
            conexiones.append(conexion_id)
            estacion_actual = estacion_anterior
        
        # Agregar el origen
        estaciones.append(origen_id)
        
        # Invertir las listas para que vayan del origen al destino
        estaciones.reverse()
        conexiones.reverse()
        
        # Obtener métricas finales
        tiempo_total, distancia_total, transbordos, costo = metricas[destino_id]
        
        # Crear objeto Ruta
        ruta = Ruta(
            estaciones=estaciones,
            conexiones=conexiones,
            tiempo_total=tiempo_total,
            distancia_total=distancia_total,
            transbordos=transbordos,
            costo=costo
        )
        
        return ruta
    
    def describir_ruta(self, ruta):
        """Genera una descripción detallada de la ruta"""
        if not ruta:
            return "No se encontró una ruta válida."
        
        descripcion = []
        descripcion.append(f"Ruta con {len(ruta.estaciones)} estaciones:")
        descripcion.append(f"- Tiempo total: {ruta.tiempo_total} minutos")
        descripcion.append(f"- Distancia total: {ruta.distancia_total:.2f} km")
        descripcion.append(f"- Transbordos: {ruta.transbordos}")
        descripcion.append(f"- Costo: {ruta.costo} unidades")
        descripcion.append("\nInstrucciones paso a paso:")
        
        linea_actual = None
        
        for i in range(len(ruta.estaciones) - 1):
            estacion_actual_id = ruta.estaciones[i]
            estacion_siguiente_id = ruta.estaciones[i + 1]
            conexion_id = ruta.conexiones[i]
            
            estacion_actual = self.base_conocimiento.estaciones[estacion_actual_id]
            estacion_siguiente = self.base_conocimiento.estaciones[estacion_siguiente_id]
            conexion = self.base_conocimiento.conexiones[conexion_id]
            
            # Si es la primera estación
            if i == 0:
                descripcion.append(f"1. Inicia en la estación {estacion_actual.nombre}.")
                descripcion.append(f"   Toma la línea {conexion.linea} en dirección a {estacion_siguiente.nombre}.")
                linea_actual = conexion.linea
            else:
                # Verificar si hay transbordo
                if conexion.linea != linea_actual:
                    descripcion.append(f"{i+1}. En la estación {estacion_actual.nombre}, transborda a la línea {conexion.linea}.")
                    linea_actual = conexion.linea
                
                # Si es la penúltima estación
                if i == len(ruta.estaciones) - 2:
                    descripcion.append(f"{i+2}. Llega a tu destino: estación {estacion_siguiente.nombre}.")
                else:
                    descripcion.append(f"{i+1}. Continúa en la línea {conexion.linea} hasta la estación {estacion_siguiente.nombre}.")
        
        return "\n".join(descripcion)

# Ejemplo de uso
def ejemplo_uso():
    # Crear la base de conocimiento
    base = BaseConocimiento("datos_transporte.json")
    
    # Crear el sistema de rutas
    sistema = SistemaRutas(base)
    
    # Definir preferencias del usuario (priorizar menos transbordos)
    preferencias = [
        Preferencia("tiempo", 0.3),
        Preferencia("transbordos", 0.5),  # Mayor peso a minimizar transbordos
        Preferencia("distancia", 0.1),
        Preferencia("costo", 0.1)
    ]
    
    # Calcular la mejor ruta
    ruta = sistema.calcular_ruta("EST001", "EST015", preferencias=preferencias)
    
    # Mostrar descripción de la ruta
    if ruta:
        print(sistema.describir_ruta(ruta))
    else:
        print("No se encontró una ruta válida.")

# Ejemplo de formato para el archivo JSON de datos
def ejemplo_json():
    datos = {
        "estaciones": [
            {
                "id": "EST001",
                "nombre": "Terminal Central",
                "latitud": 4.6097,
                "longitud": -74.0817,
                "lineas": ["L1", "L2", "L4"],
                "servicios": ["baños", "wifi", "accesibilidad"]
            },
            {
                "id": "EST002",
                "nombre": "Plaza Mayor",
                "latitud": 4.6123,
                "longitud": -74.0724,
                "lineas": ["L1"],
                "servicios": ["baños"]
            }
            # ... más estaciones
        ],
        "conexiones": [
            {
                "origen": "EST001",
                "destino": "EST002",
                "linea": "L1",
                "tiempo": 5,
                "distancia": 1.2,
                "horario": {
                    "lunes": {"inicio": [5, 0], "fin": [23, 0]},
                    "martes": {"inicio": [5, 0], "fin": [23, 0]},
                    # ... otros días
                }
            }
            # ... más conexiones
        ],
        "reglas": [
            {
                "tipo": "cierre_estacion",
                "estacion_id": "EST005",
                "fecha_inicio": "2023-06-01",
                "fecha_fin": "2023-06-15",
                "motivo": "Mantenimiento programado"
            },
            {
                "tipo": "congestion",
                "linea": "L1",
                "hora_inicio": [7, 0],
                "hora_fin": [9, 0],
                "factor": 1.8,
                "dias": ["lunes", "martes", "miercoles", "jueves", "viernes"]
            }
            # ... más reglas
        ]
    }
    return datos

if __name__ == "__main__":
    ejemplo_uso()