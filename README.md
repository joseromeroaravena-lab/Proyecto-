# CESFAM Bellavista — agenda y chatbot simulado

Prototipo académico para explorar la gestión de citas del CESFAM Bellavista
con datos ficticios. El alcance propuesto incluye agenda y panel (F1),
confirmación/cancelación (F2), recordatorios (F3), alerta con reasignación
manual (F4) e indicador de riesgo simulado (F5). Este alcance describe los
objetivos del prototipo; no implica que todas esas funciones estén implementadas
o probadas.

## Estado actual

- La interfaz de agenda está implementada con Streamlit en
  `panel_admin.py`, en la raíz del repositorio.
- Hay scripts Python para consultar SQLite, crear citas y simular una
  confirmación o cancelación.
- El panel usa `chatbot.db` junto a los scripts. En una instalación nueva,
  `crear_base.py` genera el esquema y datos ficticios de demostración.
- No se debe usar información real de pacientes ni credenciales reales.

## Requisitos

- Python 3.12
- pip

## Instalación y ejecución local

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe crear_base.py
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
ruff check --select E4,E7,E9,F conexion.py crear_base.py crear_cita.py panel_admin.py simular_respuesta.py ver_citas.py ver_pacientes.py
python -m pytest -q
python -m compileall -q conexion.py crear_base.py crear_cita.py panel_admin.py simular_respuesta.py ver_citas.py ver_pacientes.py
```

El proyecto no tiene un paso de empaquetado. La verificación de compilación es
el paso de build apropiado para estos scripts.

## Despliegue en Streamlit Community Cloud

Streamlit Community Cloud despliega desde una rama del repositorio de GitHub;
no necesita un job de deploy separado en Actions. Para que el despliegue sea
CD con validaciones previas:

1. En GitHub, configura `main` como rama de producción y agrega una regla de
   protección que exija que los jobs `Lint`, `Test` y `Build verification`
   pasen antes de fusionar cambios.
2. En Streamlit Community Cloud, conecta este repositorio y selecciona la rama
   `main` y el archivo `panel_admin.py`.
3. Streamlit instalará las dependencias desde `requirements.txt` y desplegará
   automáticamente los commits fusionados en esa rama.

**No publiques la base de trabajo ni datos reales.** Prepara una base
ficticia/sanitizada antes de conectar el repositorio a un servicio público.
El inicializador permite preparar SQLite localmente, pero todavía no se ejecuta
automáticamente durante un despliegue. El proyecto tampoco incluye persistencia
administrada por la nube; no es apto para producción y el disco del servicio no
debe considerarse persistente.

## Documentación del proyecto

- `CHANGELOG.md`: funcionalidades incorporadas, estado parcial y trabajo pendiente.

La guía de continuidad, las historias de usuario y los documentos de
planificación se mantienen fuera del repositorio. El estado publicado aquí se
describe mediante el código, el README y el changelog. F4 requiere reasignación
manual y F5 debe usar datos sintéticos y presentarse como una simulación.
