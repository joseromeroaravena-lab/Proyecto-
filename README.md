# CESFAM Bellavista — agenda y chatbot simulado

Prototipo académico para explorar la gestión de citas del CESFAM Bellavista
con datos ficticios. El alcance propuesto incluye agenda y panel (F1),
confirmación/cancelación (F2), recordatorios (F3), alerta con reasignación
manual (F4) e indicador de riesgo simulado (F5). Este alcance describe los
objetivos del prototipo; no implica que todas esas funciones estén implementadas
o probadas.

## Estado actual

La integración local con WhatsApp (FastAPI, respuestas, cola y recordatorios)
está preparada para pruebas. Consulta [WHATSAPP.md](WHATSAPP.md) para configurar
`.env`, proteger el panel y comenzar desde cero con Meta. No se ha verificado
todavía con una cuenta de Meta ni desplegado en nube. Los envíos están apagados
por defecto y limitados al número de prueba de Meta.

El nuevo modo de recordatorios con botones Confirmar/Cancelar está implementado
y probado localmente. Su plantilla separada está en revisión en Meta; la activación
y la prueba en teléfono se describen en WHATSAPP.md. El modo anterior sigue disponible.

- La interfaz de agenda está implementada con Streamlit en
  `panel_admin.py`, en la raíz del repositorio.
- La agenda incluye filtros combinables por fecha, profesional y estado. La fecha
  vacía permite ver todos los días; los selectores ofrecen Todos.
  Limpiar filtros restaura la agenda completa y Actualizar agenda conserva la
  selección. Se muestran coincidencias y total registrado por separado, y mensajes
  distintos para búsquedas sin resultados y para una agenda vacía.
- Hay scripts Python para consultar SQLite, crear citas y simular una
  confirmación o cancelación.
- El panel usa `chatbot.db` junto a los scripts. En una instalación nueva,
  `crear_base.py` genera el esquema y datos ficticios de demostración.
- No se debe usar información real de pacientes. Guardar credenciales de prueba
  únicamente en `.env`, excluido de Git.

## Requisitos

- Python 3.12
- pip

## Instalación y ejecución local

Ejecuta estos comandos en PowerShell desde la raíz del repositorio.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe crear_base.py
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Abre `.env` y establece una contraseña en `CESFAM_PANEL_PASSWORD`. Para usar
`chatbot.db`, deja `CESFAM_DB_PATH` vacía. Inicia el panel e ingresa con la
contraseña que elegiste.

```powershell
.\.venv\Scripts\python.exe -m streamlit run panel_admin.py
```

`crear_base.py` crea `chatbot.db` únicamente si no existe. El archivo continúa
excluido mediante `.gitignore` y no se publica en el repositorio. Si ya existe,
el inicializador lo conserva sin modificarlo.
No ejecutes `crear_cita.py` repetidamente: cada ejecución puede crear otra
cita. Los scripts de consulta también pueden ejecutarse desde la raíz:

```powershell
.\.venv\Scripts\python.exe conexion.py
.\.venv\Scripts\python.exe ver_pacientes.py
.\.venv\Scripts\python.exe ver_citas.py
```

## CI

GitHub Actions usa Python 3.12 para comprobar los pull requests y los pushes a
las ramas de trabajo, `beta` y `master`.

1. **Lint:** Ruff revisa los scripts Python ubicados en la raíz.
2. **Tests:** `python -m pytest -q`; utilizan una SQLite temporal y no modifican
   la base local.
3. **Build verification:** después de lint y tests, instala las dependencias de
   ejecución y compila los módulos para detectar errores de sintaxis.

Para reproducir el pipeline localmente:

```powershell
python -m pip install -r requirements-dev.txt
ruff check --select E4,E7,E9,F .
python -m pytest -q
Get-ChildItem -File -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

El proyecto no tiene un paso de empaquetado. La verificación de compilación es
el paso de build apropiado para estos scripts.

## Flujo de ramas

1. **Ramas de trabajo.** Crea una rama desde `origin/beta` con el formato
   `feature/<nombre>` o el formato numerado, como `4-feature_lista_espera`.
   Haz los commits y pushes en esa rama y abre un pull request a `beta`.
2. **`beta`, desarrollo y pruebas.** GitHub exige `Branch flow to beta`,
   `Lint`, `Test` y `Build verification` para integrar el pull request.
   Después de la fusión, el CI vuelve a probar el commit integrado en `beta`.
   Usa esa versión para las pruebas funcionales.
3. **`master`, producción.** Una vez validado el cambio, abre un pull request
   desde la rama `beta` del propio repositorio. `Branch flow to master` comprueba
   que el CI posterior a la fusión en `beta` aprobó el commit exacto del pull
   request. GitHub también comprueba el resultado de la fusión y vuelve a
   ejecutar CI una vez actualizado `master`.

Las reglas activas de GitHub exigen pull request y comprobaciones para `beta`
y `master` y bloquean los pushes directos a las dos ramas.

## Despliegue pendiente

La integración requiere FastAPI, Streamlit, un worker independiente y acceso a
la misma SQLite persistente. Publicar solo el panel no satisface esos requisitos.
La evaluación de servicios gratuitos y el respaldo local con túnel HTTPS están
en [WHATSAPP.md](WHATSAPP.md). No se ha desplegado infraestructura.

Mantener datos reales, secretos y la base de trabajo fuera de GitHub.
La etiqueta `v0.2.0` corresponde a la versión integrada para uso local.

## Documentación del proyecto

- `CHANGELOG.md`: funcionalidades incorporadas, estado parcial y trabajo pendiente.

La guía de continuidad, las historias de usuario y los documentos de
planificación se mantienen fuera del repositorio. El estado publicado aquí se
describe mediante el código, el README y el changelog. F4 requiere reasignación
manual y F5 debe usar datos sintéticos y presentarse como una simulación.
