**Universidad:** Universidad Simón Bolívar  
**Asignatura:** CI-3391 – Taller de Bases de Datos I  
**Proyecto:** API RESTful para Analítica de Videovigilancia Inteligente# API RESTful de Videovigilancia Inteligente
**Integrantes:** 
- Carlos Moreno. 21-10409
- Daniel Quijada. 20-10518
- Daniela Gragirena. 19-10543

El sistema implementa una API RESTful para la gestión y análisis de información de videovigilancia utilizando **FastAPI** y **PostgreSQL**. Permite administrar ubicaciones, cámaras y eventos, realizar consultas analíticas, buscar objetos mediante similitud vectorial e importar datos desde archivos CSV.

---

## Tecnologías utilizadas

- Python 3.10+
- FastAPI
- PostgreSQL
- psycopg
- Pydantic v2
- pgVector
- Uvicorn
- python-multipart

Las consultas a PostgreSQL se realizan directamente mediante **SQL**, sin utilizar ORM.

---

## Funcionalidades principales

El sistema permite:

- Gestionar ubicaciones.
- Gestionar cámaras de videovigilancia.
- Registrar y consultar eventos.
- Consultar tráfico detectado por cámara.
- Obtener resúmenes analíticos por zona.
- Obtener resúmenes de alertas.
- Buscar objetos visualmente similares.
- Realizar búsquedas utilizando embeddings de 512 dimensiones.
- Importar datos de videovigilancia desde archivos CSV.

---

## Estructura general

```text
Sistema-de-Vigilancia-base-de-datos-1-/
│
├── app/
│   ├── main.py
│   ├── database.py
│   │
│   ├── routers/
│   │   ├── locations.py
│   │   ├── cameras.py
│   │   ├── events.py
│   │   ├── analytics.py
│   │   ├── vectors.py
│   │   └── extra.py
│   │
│   └── schemas/
│       ├── locations.py
│       ├── cameras.py
│       ├── events.py
│       └── vectors.py
│
├── 00_extensions.sql
├── schema.sql
├── functions.sql
├── seed.sql
├── seed_100.csv
├── requirements.txt
└── README.md
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/CarlosMorenoYellow/Sistema-de-Vigilancia-base-de-datos-1-.git
cd Sistema-de-Vigilancia-base-de-datos-1-
```

---

## 2. Crear un entorno virtual

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

# Configuración de PostgreSQL

El proyecto requiere una instancia de **PostgreSQL** con soporte para la extensión **pgVector**.

La configuración utilizada actualmente por la aplicación se encuentra en:

```text
app/database.py
```

y utiliza la siguiente conexión:

```text
postgresql://usuario:password123@localhost:5432/vision_db
```

Por lo tanto, se debe disponer de una base de datos llamada:

```text
vision_db
```

con un usuario compatible con las credenciales configuradas.

Si PostgreSQL utiliza otro usuario, contraseña, puerto o nombre de base de datos, se debe modificar `DATABASE_URL` en `app/database.py`.

---

## 4. Crear la base de datos

Ejemplo utilizando `psql`:

```sql
CREATE DATABASE vision_db;
```

Luego conectarse a la base de datos:

```bash
psql -U usuario -d vision_db
```

---

## 5. Crear extensiones y estructura

Desde la raíz del proyecto, ejecutar los archivos SQL en el siguiente orden:

```bash
psql -U usuario -d vision_db -f 00_extensions.sql
psql -U usuario -d vision_db -f schema.sql
psql -U usuario -d vision_db -f functions.sql
```

Estos archivos crean las extensiones necesarias, tipos de datos, tablas, relaciones y funciones almacenadas utilizadas por la API.

---

## 6. Cargar datos de prueba

El repositorio incluye el archivo:

```text
seed_100.csv
```

Los datos pueden cargarse mediante:

```bash
psql -U usuario -d vision_db -f seed.sql
```

`seed.sql` utiliza `seed_100.csv` para poblar las tablas principales del sistema.

> Se recomienda ejecutar este comando desde la carpeta raíz del repositorio para que PostgreSQL pueda localizar correctamente el archivo CSV.

---

# Ejecutar la API

Desde la raíz del proyecto:

```bash
uvicorn app.main:app --reload
```

Por defecto, la aplicación estará disponible en:

```text
http://127.0.0.1:8000
```

Para comprobar que la API está activa:

```text
GET /
```

Respuesta esperada:

```json
{
  "message": "API de Videovigilancia activa"
}
```

---

# Documentación interactiva

FastAPI genera automáticamente documentación para probar los endpoints.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

Swagger permite ejecutar directamente las solicitudes `GET`, `POST`, `PUT` y `DELETE` desde el navegador.

---

# Endpoints principales

## Ubicaciones

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/ubicaciones` | Obtener todas las ubicaciones |
| GET | `/ubicaciones/{id}` | Obtener una ubicación por ID |
| POST | `/ubicaciones` | Crear una ubicación |
| PUT | `/ubicaciones/{id}` | Actualizar una ubicación |
| DELETE | `/ubicaciones/{id}` | Eliminar una ubicación |

Ejemplo para crear una ubicación:

```json
{
  "name": "Entrada Principal",
  "floor_no": "1",
  "zone_type": "acceso",
  "latitude": 10.4806,
  "longitude": -66.9036
}
```

---

## Cámaras

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/camaras` | Obtener todas las cámaras |
| GET | `/camaras/{id}` | Obtener una cámara por ID |
| POST | `/camaras` | Registrar una cámara |
| PUT | `/camaras/{id}` | Actualizar una cámara |

Los estados permitidos para una cámara son:

```text
activa
en_mantenimiento
inactiva
```

Ejemplo:

```json
{
  "id": "CAM-00001-01",
  "model": "Hikvision DS-2CD",
  "state": "activa",
  "has_night_vision": true,
  "lid": "UUID-DE-LA-UBICACION"
}
```

---

## Eventos

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/eventos` | Obtener todos los eventos |
| GET | `/eventos/{id}` | Obtener un evento por ID |
| POST | `/eventos` | Registrar un evento |

Ejemplo:

```json
{
  "id": 101,
  "time": "2026-07-10T14:30:00-04:00",
  "conf_level": 0.95,
  "box_x": 120,
  "box_y": 80,
  "box_w": 200,
  "box_h": 350,
  "cid": "CAM-00001-01"
}
```

El nivel de confianza (`conf_level`) debe encontrarse entre `0.0` y `1.0`.

---

# Endpoints analíticos

## Tráfico por cámara

```http
GET /analytics/cameras/{camera_id}/traffic?from=YYYY-MM-DD&to=YYYY-MM-DD
```

Ejemplo:

```text
/analytics/cameras/CAM-00001-01/traffic?from=2026-07-01&to=2026-07-15
```

Este endpoint utiliza la función almacenada:

```text
get_camera_traffic()
```

para obtener la cantidad de detecciones registradas por hora para una cámara dentro del intervalo solicitado.

---

## Resumen por zona

```http
GET /analytics/zones/{zone_type}
```

Ejemplo:

```text
/analytics/zones/estacionamiento
```

Utiliza:

```text
get_zone_summary()
```

para obtener información agregada de las ubicaciones correspondientes al tipo de zona indicado.

---

## Resumen de alertas

```http
GET /analytics/alerts/summary?days=30
```

Agrupa las alertas por:

- severidad;
- cámara;
- cantidad total.

El parámetro `days` determina el período analizado y tiene un valor predeterminado de `30`.

---

# Búsqueda vectorial

El sistema utiliza **pgVector** para comparar embeddings asociados a objetos detectados.

Cada embedding almacenado posee:

```text
512 dimensiones
```

---

## Buscar objetos similares a un objeto existente

```http
GET /objects/{object_id}/similar
```

Parámetros opcionales:

| Parámetro | Valor por defecto | Descripción |
|---|---:|---|
| `threshold` | `0.20` | Distancia máxima aceptada |
| `limit` | `5` | Máximo de resultados |

Ejemplo:

```text
/objects/UUID-DEL-OBJETO/similar?threshold=0.20&limit=5
```

La consulta utiliza internamente la función:

```text
find_similar_objects()
```

y retorna los objetos similares junto con su distancia y contexto de detección.

---

## Buscar mediante un embedding externo

```http
POST /search/similar
```

El cuerpo de la solicitud debe contener un vector de **exactamente 512 valores**.

```json
{
  "vector": [0.12, 0.34, 0.56],
  "tipo": "persona",
  "limit": 10
}
```

> El ejemplo anterior muestra únicamente la estructura. El campo `vector` debe contener exactamente 512 valores numéricos.

El campo `tipo` es opcional y acepta:

```text
persona
vehiculo
```

La API ordena los resultados según su distancia vectorial, colocando primero los objetos más similares.

---

# Importación mediante CSV

El sistema también incluye un endpoint para importar información desde archivos CSV:

```http
POST /csv
```

El archivo se envía utilizando `multipart/form-data`.

La importación puede procesar información relacionada con:

- ubicaciones;
- cámaras;
- eventos;
- objetos;
- relaciones entre eventos y objetos;
- alertas.

Entre las columnas mínimas requeridas se encuentran:

```text
ubicacion_nombre
camara_nombre
evento_id
evento_marca_tiempo
evento_confianza
objeto_tipo
```

El resultado de la operación posee la siguiente estructura:

```json
{
  "added": 10,
  "updated": 2,
  "rejected": 1,
  "errors": []
}
```

donde:

- `added`: filas nuevas agregadas;
- `updated`: filas correspondientes a eventos existentes que fueron actualizados;
- `rejected`: filas que no pudieron ser procesadas;
- `errors`: detalle de los errores encontrados.

---

# Pruebas de la API

La forma recomendada de probar la aplicación es mediante:

```text
http://127.0.0.1:8000/docs
```

También pueden realizarse solicitudes desde herramientas como Postman o mediante `curl`.

Ejemplo:

```bash
curl http://127.0.0.1:8000/ubicaciones
```

Consulta de cámaras:

```bash
curl http://127.0.0.1:8000/camaras
```

Consulta de eventos:

```bash
curl http://127.0.0.1:8000/eventos
```

Consulta analítica:

```bash
curl "http://127.0.0.1:8000/analytics/alerts/summary?days=30"
```

---

# Modelo general de datos

La base de datos administra principalmente las siguientes entidades:

```text
LOCATION
   │
   └── CAMERA
          │
          └── EVENT
                 │
                 ├── ALERT
                 │
                 └── IDENTIFIES
                         │
                         └── OBJECT
```

Los objetos pueden corresponder a:

```text
persona
vehiculo
```

y pueden almacenar un embedding `VECTOR(512)` utilizado para las búsquedas por similitud.

