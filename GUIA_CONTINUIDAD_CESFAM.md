# Guía de continuidad — Chatbot CESFAM Bellavista

**Proyecto de Título AINC422 | Actualización: 18/10/2026**  
**Documento base:** `Propuesta_MVP_Jose_Romero_v2.docx` (propuesta del docente Marcelo Martínez Espinoza).  
**Propósito:** retomar el proyecto en Visual Studio Code sin perder contexto, respetando el alcance y los plazos académicos.

> **Estado real:** prototipo local en desarrollo. La conexión Python–SQLite y el registro de una cita ficticia funcionan. No se ha confirmado chatbot operativo, panel web, GitHub, WhatsApp ni despliegue.

## 1. Alcance oficial del MVP: F1 a F5

| Función | Alcance establecido en la propuesta docente | Fecha objetivo |
|---|---|---|
| **F1** | Agenda simulada de **pacientes, profesionales y citas**, más **panel administrativo** para consultar citas y sus estados. | Sumativa 2, **24/11** |
| **F2** | Chatbot para **confirmar o cancelar** citas, **registrando cada respuesta**. | Sumativa 2, **24/11** |
| **F3** | Recordatorios automáticos **72 y 24 horas** antes de cada cita. | Sumativa 2, **24/11** |
| **F4** | La cancelación **libera la hora y genera una alerta** en el panel para que el personal **reasigne manualmente** desde la lista de espera. | Sumativa 3, **15/12** |
| **F5** | Indicador de riesgo de inasistencia por paciente, con un modelo sencillo entrenado con **datos sintéticos**. | Sumativa 3, **15/12** |

### Fuera del MVP

- Integración con la agenda real del CESFAM y uso de datos reales de pacientes.
- Reagendamiento desde el chatbot y **reasignación automática** de horas: F4 es **alerta + decisión administrativa manual**.
- Demostrar una reducción real de 25 % de inasistencias durante el curso. Se evaluará el prototipo con escenarios y datos simulados.

**Corrección importante respecto de ideas exploradas en el chat:** no desarrollar la oferta automática por WhatsApp al siguiente paciente como obligación del MVP. Las tablas `offers` y `outbox` ya existen, pero deben adaptarse al alcance docente.

## 2. Fechas y entregables

| Entrega | Fecha | Qué exige |
|---|---|---|
| **Sumativa 1** | **27/10/2026** | Historias de usuario/casos de uso, alcance, herramientas, gestión de configuración, cronograma con metodología, **100 % de mockups F1–F5**, modelo de datos e **inicio de F1 en el repositorio**. |
| **Sumativa 2** | **24/11/2026** | F1–F3 desplegadas (60 %), instructivo de instalación, pruebas unitarias y de integración, control de versiones. |
| **Sumativa 3** | **15/12/2026** | F1–F5 desplegadas, pruebas unitarias, de integración y de aceptación. |
| Examen | 16/12–29/12 | Presentación ante comisión. |

**Prioridad actual:** terminar los documentos y mockups de Sumativa 1 y subir el inicio de F1 a GitHub. No es necesario terminar WhatsApp antes del 27/10.

## 3. Entorno local confirmado

- **Windows**, **Visual Studio Code** instalado.
- **Python 3.12.0** y **pip 23.2.1** comprobados.
- **DB Browser for SQLite** instalado.
- Carpeta del proyecto: `C:\Users\joser\OneDrive\Documentos\Chatbot_`
- Base de datos: `C:\Users\joser\OneDrive\Documentos\Chatbot_\chatbot.db`
- Python ejecutable: `C:\Users\joser\AppData\Local\Programs\Python\Python312\python.exe`

### Ejecutar scripts desde PowerShell de VS Code

```powershell
& "C:\Users\joser\AppData\Local\Programs\Python\Python312\python.exe" --version
& "C:\Users\joser\AppData\Local\Programs\Python\Python312\python.exe" conexion.py
& "C:\Users\joser\AppData\Local\Programs\Python\Python312\python.exe" ver_pacientes.py
& "C:\Users\joser\AppData\Local\Programs\Python\Python312\python.exe" ver_citas.py
```

**Nota:** `python` y `py` no se reconocían en la terminal integrada, aunque `py` funcionó en CMD externo. La **ruta completa** sí funcionó. En PowerShell se requiere el prefijo **`&`** para ejecutar una ruta entre comillas. Para configurar el intérprete: `Ctrl+Shift+P` → `Python: Select Interpreter` → seleccionar `Python312\python.exe`.

## 4. Archivos y avances reales

```text
/
├── conexion.py
├── ver_pacientes.py
├── ver_citas.py
├── crear_cita.py
├── panel_admin.py
└── simular_respuesta.py
```

El 10/11/2026 los scripts y la configuración de VS Code se trasladaron desde
`Chatbot_/` a la raíz del repositorio. La base SQLite no está incluida en esa
carpeta de código; `conexion.py` espera `chatbot.db` junto al propio script.

**Pruebas confirmadas:**

1. `conexion.py` conectó correctamente y encontró las tablas `appointments`, `offers`, `outbox`, `patients`, `waitlist` y la tabla interna `sqlite_sequence`.
2. `ver_pacientes.py` consultó correctamente pacientes.
3. `ver_citas.py` mostró inicialmente **0 citas**.
4. `crear_cita.py` registró una cita ficticia; el usuario confirmó que quedó todo correcto.
5. **No se ha confirmado** la ejecución de `cancelar_cita.py`, ni recordatorios, reasignaciones, modelo predictivo o WhatsApp.

### Cita de prueba

- Paciente: `patient_id=1` (ficticio).
- Especialidad: `Medicina General`.
- Profesional ficticia: `Dra. Ana Martínez`.
- Fecha: `2026-10-26 10:00`.
- Estado inicial: `scheduled`.
- **Consultar ID real** con `ver_citas.py` antes de modificarla.
- **No volver a ejecutar `crear_cita.py` sin necesidad:** crea otra cita y puede duplicar registros.

## 5. Modelo SQLite implementado

La base se creó **manualmente** en DB Browser. Verificar el esquema real antes de refactorizar o documentar restricciones.

### `patients`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `name TEXT NOT NULL`
- `phone TEXT NOT NULL UNIQUE`
- `email TEXT`
- `consent_whatsapp INTEGER`
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP`

Existe al menos un paciente ficticio con `id=1`. Una fila antigua tenía `created_at=NULL`: el valor por defecto no modifica filas anteriores.

### `appointments`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `patient_id INTEGER NOT NULL` → FK `patients(id)`
- `specialty TEXT`
- `professional TEXT`
- `appointment_date TEXT`
- `status TEXT DEFAULT 'scheduled'`
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP`

Se recomendó `NOT NULL` para especialidad, profesional y fecha, pero **verificar si efectivamente se aplicó**.

### `waitlist`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `patient_id INTEGER NOT NULL` → FK `patients(id)`
- `specialty TEXT NOT NULL`
- `priority INTEGER DEFAULT 0`
- `status TEXT NOT NULL DEFAULT 'waiting'`
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP`

Se registró un ejemplo con `patient_id=1` y `Medicina General`. **Para probar una reasignación realista, crear un segundo paciente ficticio**, diferente al titular de la cita.

### `offers`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `appointment_id INTEGER NOT NULL` → FK `appointments(id)`
- `patient_id INTEGER NOT NULL` → FK `patients(id)`
- `status TEXT NOT NULL DEFAULT 'pending'`
- `expires_at TEXT`
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP`

Las dos FK se comprobaron mediante captura. Su existencia **no implica** que deba haber reasignación automática.

### `outbox`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `patient_id INTEGER NOT NULL` → FK `patients(id)`
- `appointment_id INTEGER` → FK `appointments(id)` (opcional)
- `message TEXT NOT NULL`
- `status TEXT NOT NULL DEFAULT 'pending'`
- `created_at TEXT DEFAULT CURRENT_TIMESTAMP`
- `sent_at TEXT`

El usuario confirmó la creación de la tabla.

### Consultas para verificar el esquema real

En DB Browser → **Execute SQL**:

```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
PRAGMA table_info(patients);
PRAGMA table_info(appointments);
PRAGMA table_info(waitlist);
PRAGMA table_info(offers);
PRAGMA table_info(outbox);
PRAGMA foreign_key_list(appointments);
PRAGMA foreign_key_list(waitlist);
PRAGMA foreign_key_list(offers);
PRAGMA foreign_key_list(outbox);
```

### Cambios de diseño a evaluar (todavía NO implementados)

- **F1:** normalizar profesionales en una tabla `professionals` o justificar el campo `professional` actual; construir panel web.
- **F2:** tabla de **respuestas entrantes** por cita/paciente/fecha/resultado; `outbox` solo registra mensajes salientes.
- **F3:** registrar tipo de recordatorio `72h`/`24h`, horario y prevención de duplicados.
- **F4:** tabla/registro de **alertas administrativas** y reasignaciones manuales; garantizar transacciones.
- **F5:** campos o tabla de puntajes de riesgo, versión de modelo y fecha de cálculo; datos sintéticos.
- **Integridad:** activar `PRAGMA foreign_keys=ON` en cada conexión, validar estados y evitar asignaciones simultáneas.

## 6. Código de referencia y consultas

Patrón **sugerido** para una futura refactorización (no necesariamente es el contenido actual de `conexion.py`):

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chatbot.db"

def conectar():
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Base de datos no encontrada: {DB_PATH}")
    conexion = sqlite3.connect(DB_PATH, timeout=10)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion
```

Consulta de citas utilizada:

```sql
SELECT a.id, p.name, a.specialty, a.professional,
       a.appointment_date, a.status
FROM appointments AS a
JOIN patients AS p ON a.patient_id = p.id
ORDER BY a.appointment_date;
```

Cancelación **propuesta, no probada**:

```sql
UPDATE appointments
SET status = 'cancelled'
WHERE id = ? AND status = 'scheduled';
```

Validar `cursor.rowcount == 1` y realizar `commit()`. **No borrar físicamente la cita**; conservar historial. La alerta administrativa de F4 se desarrollará después.

## 7. Problemas técnicos ya resueltos

| Error | Solución |
|---|---|
| `python` no reconocido | Ejecutar Python mediante la ruta completa. |
| `py` no reconocido dentro de VS Code | Usar `Python312\python.exe` directamente. |
| PowerShell: `Token 'ver_pacientes.py' inesperado` | Agregar `&` al inicio del comando. |
| `ver_pacientes.py` ejecutaba sin mostrar nada | Revisar contenido, guardar con `Ctrl+S` y volver a ejecutar. |
| `sqlite3.OperationalError: database is locked` | En DB Browser: **Write Changes**, **File → Close Database** y cerrar DB Browser antes de escribir desde Python. |
| `created_at` en `NULL` en registro antiguo | No es pérdida de datos; el valor por defecto no se aplica retroactivamente. |

**Precaución:** la base está dentro de **OneDrive**; hacer copia de seguridad antes de cambios de esquema y evitar escrituras concurrentes. **Cerrar DB Browser no elimina la base de datos.**

## 8. Sumativa 1: documentos que faltan

### Historias de usuario F1–F5

Formato: **Como** [rol], **quiero** [acción], **para** [beneficio]. Agregar ID, prioridad y criterios de aceptación comprobables en formato **Dado / Cuando / Entonces**. Roles: paciente, administrativo/a, encargado/a del sistema. **Aún no están redactadas como entregable final.**

### Cinco mockups (100 % requeridos al 27/10)

1. **F1:** agenda y panel administrativo (pacientes, profesionales, citas, filtros, estados).
2. **F2:** interfaz/conversación CONFIRMAR–CANCELAR y registro de respuestas.
3. **F3:** recordatorios programados a 72/24 horas y estado de envíos.
4. **F4:** alerta de cupo liberado y **reasignación manual** desde lista de espera.
5. **F5:** indicador de riesgo de inasistencia por paciente, claramente simulado.

### Modelo de datos

Diagrama entidad–relación, PK/FK, cardinalidades, diccionario de datos. **Distinguir lo implementado de lo propuesto** para cubrir F1–F5.

### Cronograma

Metodología ágil/Scrum adaptada, actividades, dependencias, responsables, pruebas y los hitos 27/10, 24/11 y 15/12.

### Gestión de configuración / GitHub

**No hay evidencia confirmada de un repositorio Git creado.** Verificar `git --version`, configurar Git y crear repositorio. Incluir `README.md`, `.gitignore`, código inicial de F1 y documentación. No subir tokens, `.env`, datos reales ni `chatbot.db` de trabajo.

`.gitignore` recomendado:

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
.env.*
*.db
*.sqlite
*.sqlite3
*.db-journal
*.db-wal
*.db-shm
```

Para reproducibilidad, publicar **esquema SQL y datos de prueba ficticios**, no la base de trabajo.

## 9. Arquitectura futura y API de WhatsApp

```text
Panel administrativo ──────┐
                           ├── Backend FastAPI/Python ── Base de datos
Canal chatbot de prueba ───┘          │
                                     ├── F1 Agenda
                                     ├── F2 Confirmación/cancelación
                                     ├── F3 Recordatorios 72h y 24h
                                     ├── F4 Alerta y reasignación MANUAL
                                     └── F5 Riesgo de inasistencia
```

**WhatsApp Cloud API es técnicamente posible, pero NO está integrada.** Requerirá Meta for Developers, WhatsApp Business Platform, credenciales seguras, webhook HTTPS, plantillas aprobadas cuando correspondan, consentimiento y pruebas con números autorizados. La propuesta docente recomienda **decidir entre entorno de prueba de WhatsApp o canal alternativo más simple** para no frenar el avance. FastAPI, panel y base de datos deben desplegarse en la nube desde Sumativa 2. **SQLite local no equivale a una base desplegada en producción**; revisar persistencia del hosting o eventual migración.

**Seguridad sanitaria:** solo datos ficticios/sintéticos; no publicar información personal ni clínica; minimizar contenido de mensajes; controlar acceso al panel y registrar auditoría.

## 10. Próximas tareas, en orden

### Antes del 27/10 — prioridad máxima

- [ ] Confirmar que la propuesta MVP v2 fue acordada con el docente.
- [ ] Redactar historias de usuario F1–F5 y criterios de aceptación.
- [ ] Crear los **cinco mockups**.
- [ ] Verificar SQLite y producir modelo entidad–relación/diccionario.
- [ ] Documentar alcance, herramientas y gestión de configuración.
- [ ] Preparar cronograma con metodología.
- [ ] Iniciar F1 en GitHub con README y commits.
- [ ] Revisar y entregar Sumativa 1.

### 28/10–24/11 — Sumativa 2

- [ ] Completar F1 (agenda y panel).
- [ ] Implementar F2 (chatbot y registro de respuestas).
- [ ] Implementar F3 (recordatorios 72/24h, sin duplicados).
- [ ] Probar canal elegido; desplegar FastAPI, panel y BD.
- [ ] Preparar instructivo, pruebas y control de versiones.

### 25/11–15/12 — Sumativa 3

- [ ] Implementar F4 (alerta y reasignación manual).
- [ ] Implementar F5 (modelo simple con datos sintéticos).
- [ ] Ejecutar pruebas unitarias, integración y aceptación.
- [ ] Preparar demostración y presentación final.

## 11. Instrucción para retomar el proyecto en VS Code

Al abrir una nueva conversación o asistente en VS Code, compartir este `.md` y escribir:

> Continúa el proyecto CESFAM Bellavista siguiendo `GUIA_CONTINUIDAD_CESFAM.md`. Respeta el alcance oficial F1–F5 y las fechas de Sumativas. Inspecciona primero los archivos existentes y el esquema real de `chatbot.db` antes de modificar código. Guíame paso a paso en Windows/VS Code. Usa solo datos ficticios. F4 exige alerta y reasignación **manual**, no automática. La prioridad actual es Sumativa 1 e iniciar F1 en GitHub. No afirmes que una funcionalidad está probada si solo se entregó el código.

**Forma de trabajo preferida:** pasos pequeños, comandos exactos, esperar confirmación o captura antes de continuar.

---

**Trazabilidad:** alcance y fechas tomados de `Propuesta_MVP_Jose_Romero_v2.docx` (págs. 1–2); estado técnico y problemas resueltos recopilados del chat hasta el 18/10/2026. La aceptación final del MVP por el docente y el estado actual del repositorio aún deben confirmarse.
