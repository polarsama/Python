# Sistema de Rutas para Transporte Masivo

Este proyecto implementa un sistema inteligente para encontrar la mejor ruta entre dos puntos en un sistema de transporte masivo, utilizando una base de conocimiento con reglas lógicas y el algoritmo A*.

## Características

- Cálculo de rutas óptimas entre estaciones
- Aplicación de reglas lógicas (cierres, mantenimiento, congestión)
- Personalización de preferencias (tiempo, distancia, transbordos, costo)
- Consideración de horarios y frecuencias de transporte
- Instrucciones detalladas paso a paso para cada ruta

## Requisitos

- Python 3.7 o superior
- No requiere bibliotecas externas (solo utiliza módulos de la biblioteca estándar)

## Instalación

1. Clone el repositorio o descargue los archivos:
   ```

   ```

2. No se requiere ninguna instalación adicional.

## Estructura de archivos

- `main.py`: Código principal del sistema
- `datos.json`: Archivo de datos con la información del sistema de transporte
- `README.md`: Este archivo de documentación

## Uso básico

1. Prepare su archivo de datos JSON siguiendo el formato especificado (ver sección "Formato de datos").

2. Importe y utilice el sistema en su código:

```python
from sistema_rutas import BaseConocimiento, SistemaRutas, Preferencia

# Crear la base de conocimiento
base = BaseConocimiento("datos_transporte.json")

# Crear el sistema de rutas
sistema = SistemaRutas(base)

# Calcular la mejor ruta entre dos estaciones
ruta = sistema.calcular_ruta("EST001", "EST015")

# Mostrar descripción de la ruta
if ruta:
    print(sistema.describir_ruta(ruta))
else:
    print("No se encontró una ruta válida.")
```

## Personalización de preferencias

Puede personalizar las preferencias para dar más importancia a ciertos criterios:

```python
# Definir preferencias personalizadas (priorizar menos transbordos)
preferencias = [
    Preferencia("tiempo", 0.3),
    Preferencia("transbordos", 0.5),  # Mayor peso a minimizar transbordos
    Preferencia("distancia", 0.1),
    Preferencia("costo", 0.1)
]

# Calcular ruta con preferencias personalizadas
ruta = sistema.calcular_ruta("EST001", "EST015", preferencias=preferencias)
```

## Consideración de horarios

Para calcular rutas considerando la hora actual:

```python
import datetime

# Obtener hora actual
hora_actual = datetime.datetime.now()

# O especificar una hora concreta
hora_especifica = datetime.datetime(2023, 6, 1, 8, 30)  # 1 de junio a las 8:30

# Calcular ruta considerando horarios
ruta = sistema.calcular_ruta("EST001", "EST015", hora=hora_especifica)
```

## Formato de datos

El sistema utiliza un archivo JSON con la siguiente estructura:

```json
{
    "estaciones": [
        {
            "id": "EST001",
            "nombre": "Terminal Central",
            "latitud": 4.6097,
            "longitud": -74.0817,
            "lineas": ["L1", "L2", "L4"],
            "servicios": ["baños", "wifi", "accesibilidad"]
        },
        ...
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
                ...
            }
        },
        ...
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
        },
        ...
    ]
}
```

### Tipos de reglas soportadas

1. **cierre_estacion**: Cierra completamente una estación
2. **cierre_linea**: Cierra una línea completa
3. **mantenimiento_tramo**: Cierra un tramo específico entre dos estaciones
4. **congestion**: Aumenta el tiempo de viaje en ciertas líneas en horarios específicos

## Ejemplo completo

```python
import datetime
from sistema_rutas import BaseConocimiento, SistemaRutas, Preferencia

# Crear la base de conocimiento
base = BaseConocimiento("datos.json")

# Crear el sistema de rutas
sistema = SistemaRutas(base)

# Definir preferencias del usuario
preferencias = [
    Preferencia("tiempo", 0.4),
    Preferencia("transbordos", 0.4),
    Preferencia("distancia", 0.1),
    Preferencia("costo", 0.1)
]

# Especificar hora (hora pico de la mañana)
hora = datetime.datetime(2023, 6, 1, 8, 30)

# Calcular la mejor ruta
ruta = sistema.calcular_ruta("EST001", "EST015", hora=hora, preferencias=preferencias)

# Mostrar descripción de la ruta
if ruta:
    print(sistema.describir_ruta(ruta))
else:
    print("No se encontró una ruta válida.")
```

## Creación de un archivo de datos de ejemplo

Para crear un archivo de datos de ejemplo, puede utilizar el siguiente código:

```python
import json
from sistema_rutas import ejemplo_json

# Generar datos de ejemplo
datos = ejemplo_json()

# Guardar en un archivo
with open("datos_transporte.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("Archivo de datos de ejemplo creado: datos_transporte.json")
```

## Limitaciones actuales

- El sistema asume que todas las estaciones están correctamente conectadas
- La estimación de tiempo no considera el tiempo de espera entre vehículos
- No maneja múltiples tipos de servicios (express, local) en la misma línea

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abra un issue para discutir cambios importantes antes de enviar un pull request.

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).
