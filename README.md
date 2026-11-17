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

- La interfaz de agenda está implementada con Streamlit en
  `panel_admin.py`, en la raíz del repositorio.
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

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe crear_base.py
Copy-Item -LiteralPath .env.example -Destination .env
# Editar .env: establecer CESFAM_PANEL_PASSWORD antes de abrir el panel.
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

GitHub Actions ejecuta estas verificaciones en pull requests y en pushes a
`main` o `master`, usando Python 3.12:

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

## Despliegue pendiente

La integración requiere FastAPI, Streamlit, un worker independiente y acceso a
la misma SQLite persistente. Publicar solo el panel no satisface esos requisitos.
La evaluación de servicios gratuitos y el respaldo local con túnel HTTPS están
en [WHATSAPP.md](WHATSAPP.md). No se ha desplegado infraestructura.

Mantener el flujo `feature → beta → master`; no publicar datos reales, secretos
ni la base de trabajo. No crear `v0.2.0` hasta validar la entrega integrada.

## Documentación del proyecto

- `CHANGELOG.md`: funcionalidades incorporadas, estado parcial y trabajo pendiente.

La guía de continuidad, las historias de usuario y los documentos de
planificación se mantienen fuera del repositorio. El estado publicado aquí se
describe mediante el código, el README y el changelog. F4 requiere reasignación
manual y F5 debe usar datos sintéticos y presentarse como una simulación.
