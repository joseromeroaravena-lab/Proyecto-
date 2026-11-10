# CESFAM Bellavista — agenda y chatbot simulado

Prototipo académico para explorar la gestión de citas del CESFAM Bellavista
con datos ficticios. El alcance propuesto incluye agenda y panel (F1),
confirmación/cancelación (F2), recordatorios (F3), alerta con reasignación
manual (F4) e indicador de riesgo simulado (F5). La guía y las historias de
usuario describen requisitos; no implican que todas esas funciones estén
implementadas o probadas.

## Estado actual

- La interfaz de agenda está implementada con Streamlit en
  `Chatbot_/panel_admin.py`.
- Hay scripts Python para consultar SQLite, crear citas y simular una
  confirmación o cancelación.
- El panel requiere una base de datos SQLite con el esquema esperado y usa
  `Chatbot_/chatbot.db` por defecto.
- No se debe usar información real de pacientes ni credenciales reales.

## Requisitos

- Python 3.12
- pip

## Instalación y ejecución local

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run Chatbot_/panel_admin.py
```

La aplicación necesita `Chatbot_/chatbot.db`. `.gitignore` evita agregar bases
locales nuevas por accidente; la base existente ya está seguida por Git y no
deja de estarlo al agregar esta regla. Prepara una base de demostración con
datos estrictamente ficticios antes de ejecutar el panel en un entorno limpio.
No ejecutes `crear_cita.py` repetidamente: cada ejecución puede crear otra
cita. Los scripts de consulta también pueden ejecutarse desde la raíz:

```powershell
python Chatbot_/conexion.py
python Chatbot_/ver_pacientes.py
python Chatbot_/ver_citas.py
```

## CI

GitHub Actions ejecuta estas verificaciones en pull requests y en pushes a
`main` o `master`, usando Python 3.12:

1. **Lint:** `ruff check --select E4,E7,E9,F Chatbot_ tests`.
2. **Tests:** `python -m pytest -q`; utilizan una SQLite temporal y no modifican
   la base local.
3. **Build verification:** después de lint y tests, instala las dependencias de
   ejecución y compila los módulos para detectar errores de sintaxis.

Para reproducir el pipeline localmente:

```powershell
python -m pip install -r requirements-dev.txt
ruff check --select E4,E7,E9,F Chatbot_ tests
python -m pytest -q
python -m compileall -q Chatbot_
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
   `main` y el archivo `Chatbot_/panel_admin.py`.
3. Streamlit instalará las dependencias desde `requirements.txt` y desplegará
   automáticamente los commits fusionados en esa rama.

**No publiques la base de trabajo ni datos reales.** La base `Chatbot_/chatbot.db`
ya estaba seguida por Git antes de agregar `.gitignore`; el ignore no deja de
seguir archivos existentes ni los elimina del historial. Comprueba y prepara
una base ficticia/sanitizada antes de conectar el repositorio a un servicio
público. Además, el código actual espera ese archivo SQLite local y no incluye
provisión de base ni persistencia administrada por la nube; el despliegue no es
apto para producción y el disco del servicio no debe considerarse persistente.

## Documentación del proyecto

- `CHANGELOG.md`: funcionalidades incorporadas, estado parcial y trabajo pendiente.
- `GUIA_CONTINUIDAD_CESFAM.md`: alcance, estado técnico y plan de continuidad.
- `docs/HISTORIAS_USUARIO.md`: historias y criterios de aceptación.

Estas fuentes delimitan el MVP; F4 requiere reasignación manual y F5 debe usar
datos sintéticos y presentarse como una simulación.
