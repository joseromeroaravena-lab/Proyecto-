# WhatsApp: instalación y demostración desde cero

Implementación académica con pacientes ficticios. No se han habilitado cuentas,
números ni servicios externos automáticamente. Los envíos están bloqueados por
defecto y el código solo permite habilitar el emisor de prueba de Meta. Un número
propio requiere revisar sus condiciones; no habilitarlo simulando que es de prueba.

## 1. Qué estamos conectando

- **API:** una dirección de Meta a la que Python solicita enviar un mensaje.
- **WhatsApp Business Account (WABA):** cuenta que agrupa los recursos de WhatsApp.
  No es lo mismo que instalar la aplicación WhatsApp Business en un teléfono.
- **Phone Number ID:** identificador técnico del emisor; no es su número telefónico.
- **Access token:** credencial para pedir envíos. Puede vencer o ser revocada.
- **App secret:** secreto con que validamos que los eventos vienen de Meta.
- **Webhook:** dirección HTTPS de nuestra aplicación que recibe mensajes y estados.
  El token de verificación del webhook lo eliges tú; no reemplaza al access token.
- **Plantilla:** mensaje aprobado por Meta para los casos en que exige una plantilla.
  Los recordatorios usan una plantilla; no se intenta eludir las reglas con texto libre.

Flujo: teléfono → Meta → webhook FastAPI → SQLite → worker → Meta → teléfono.
Streamlit permite consultar citas, consentimiento, respuestas y envíos.

## 2. Preparar el proyecto local

Ejecuta estos comandos en PowerShell desde la raíz del repositorio.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Si `.env` ya existe, conservarlo y agregar las claves faltantes manualmente.
Editar `.env` y establecer una contraseña administrativa larga y exclusiva en
`CESFAM_PANEL_PASSWORD`. Dejar `WA_SEND_ENABLED` y `WA_TEST_NUMBER_CONFIRMED`
vacíos o en `0` durante la configuración inicial.

Si no existe la base:

```powershell
.\.venv\Scripts\python.exe crear_base.py
```

Si ya existe, cerrar DB Browser, detener panel/API/worker y ejecutar:

```powershell
.\.venv\Scripts\python.exe migrar_whatsapp.py
```

La migración crea primero una copia mediante la API de respaldo SQLite en
`backups/`. Agrega tablas `whatsapp_inbound`, `whatsapp_outbox`, eventos de estado
y control de migración; conserva el historial de `appointment_responses` y la
tabla `outbox` anterior. La cola nueva permite registrar entradas inválidas sin
romper las restricciones de la simulación antigua. Repetir la migración es seguro.
Una instalación nueva incluye estas tablas automáticamente.

Para otra ubicación, configurar `CESFAM_DB_PATH` como ruta absoluta y crear la
base con `crear_base.py --ruta 'C:/ruta/chatbot.db'`. Todos los procesos deben usar
la misma base. En Windows, mantener el archivo fuera de carpetas sincronizadas
para demostraciones prolongadas. No abrir escrituras desde DB Browser a la vez.

## 3. Crear el entorno de prueba en Meta

1. Abrir [Meta for Developers](https://developers.facebook.com/) e iniciar sesión
   con tu cuenta. Completar personalmente verificaciones de identidad o acceso.
2. Crear una aplicación para el caso de uso WhatsApp y seguir la configuración de
   WhatsApp Business Platform. Los nombres de las pantallas pueden variar.
3. En la configuración de API, seleccionar el emisor de **prueba proporcionado
   por Meta**. Agregar tu teléfono receptor y completar su verificación.
4. Enviar desde la herramienta de Meta el mensaje de prueba disponible, habitualmente
   `hello_world`. Comprobar que llega al teléfono antes de continuar.
5. Guardar privadamente en `.env` el Phone Number ID, access token, App secret y
   versión de Graph API que indique la consola. Crear un `WA_VERIFY_TOKEN` aleatorio.
6. No agregar medios de pago ni activar productos con cobro. Si Meta exige pago,
   detener ese paso. No compartir tokens, códigos SMS ni capturas que los expongan.

Referencia: [Developer Hub oficial](https://whatsappbusiness.com/developers/developer-hub/).
La documentación detallada de developers.facebook.com devolvió bloqueo de acceso
automatizado durante esta implementación: validar los pasos exactos en tu consola.

## 4. Levantar API y conectar el webhook

Primera terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn whatsapp_api:app --host 127.0.0.1 --port 8000 --no-access-log
```

`--no-access-log` evita registrar el token de verificación incluido en la URL.
En otra terminal, una vez instalado `cloudflared` desde su documentación oficial:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Registrar en Meta `https://<URL-asignada>/webhooks/whatsapp` y el valor de
`WA_VERIFY_TOKEN`. Suscribir los eventos `messages` para recibir mensajes y estados.
El GET devuelve el desafío de verificación; el POST valida `X-Hub-Signature-256`
contra el cuerpo original y solo procesa el Phone Number ID configurado.

No tunelizar el puerto del panel. Los Quick Tunnels son temporales y no equivalen
a despliegue permanente. Al cambiar su URL hay que actualizar Meta.
[Guía oficial de Cloudflare](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## 5. Asociar el teléfono y probar respuestas

Segunda terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run panel_admin.py --server.address 127.0.0.1
```

Ingresar con la contraseña configurada. Registrar un paciente ficticio cuyo
teléfono sea el receptor autorizado, con formato `+56912345678`, y crear una cita
futura. No usar el nombre de una persona real. Guardar su consentimiento en el panel.

Desde el teléfono escribir `1` para confirmar o `2` para cancelar si hay una sola
cita activa futura. Con varias citas, usar Responder sobre el recordatorio recibido
o indicar la referencia: `1 <ID>` o `2 <ID>`. Se siguen aceptando `CONFIRMAR <ID>`
y `CANCELAR <ID>`. Las citas ajenas o pasadas no se modifican.
Para repetir una acción sobre una cita cancelada, indicar su ID explícitamente.

El webhook registra los resultados aunque los envíos estén deshabilitados.
Para recibir los acuses, configurar en `.env`:

```text
WA_SEND_ENABLED=1
WA_TEST_NUMBER_CONFIRMED=1
WA_ALLOWED_RECIPIENTS=+56912345678
```

Hacerlo solamente tras comprobar que el emisor es de prueba y que la prueba no
requiere gasto. Reiniciar los procesos después de cambiar `.env`.
Tercera terminal:

```powershell
.\.venv\Scripts\python.exe recordatorios.py
```

El worker trabaja independientemente del panel, con ciclos cada 60 segundos mientras
el procesamiento no exceda ese tiempo. No superpone ciclos; envíos lentos pueden
retrasar el siguiente. Un candado evita dos workers sobre la misma base. `--once` ejecuta un
solo ciclo. Si se cierra la terminal, se suspende Windows o se apaga el equipo,
dejan de procesarse envíos. El botón de actualizar del panel permite ver cambios.

## 6. Recordatorios y estados

El modo de texto anterior se mantiene con `WA_REMINDER_BUTTONS=0` (predeterminado).
El modo de botones se describe al final de esta sección.

Configurar `WA_REMINDER_TEMPLATE` y `WA_TEMPLATE_LANGUAGE` con una plantilla aprobada
para esa cuenta, cuyo cuerpo tenga cuatro parámetros de texto en este orden:
profesional y especialidad, fecha local DD/MM/AAAA, hora HH:MM y referencia de cita.
Ejemplo de cuerpo a presentar a Meta:

```text
Tienes una cita médica con {{1}} el {{2}} a las {{3}}.

Responde con una opción:
1. Confirmar asistencia
2. Cancelar cita

Referencia de tu cita: {{4}}.
Demostración académica con datos ficticios.
```

Ejemplos: `Dra. Ana Martínez (Medicina General)`, `20/11/2026`, `10:00`, `10`.
WA_TEMPLATE_LANGUAGE debe coincidir con el código del idioma aprobado por Meta.
Las plantillas anteriores de dos variables no son compatibles con este formato.

La aprobación y disponibilidad en la cuenta de prueba no están garantizadas.
`hello_world` sirve para conectividad y no sustituye esta plantilla. Sin ella, los
recordatorios quedan `blocked_template`, consultables en el panel, sin llamar a Meta.
Después de corregir un bloqueo terminal se requiere revisión técnica; no se
reencola automáticamente ni se regeneran duplicados.

- Los horarios de cita se interpretan en `America/Santiago`; los eventos se guardan
  en UTC. Los umbrales representan 72/24 horas transcurridas, incluso con cambio de hora.
- Solo se generan umbrales posteriores o iguales a la creación de la cita.
  Tras una interrupción se genera únicamente el vencido más reciente.
- Antes de enviar se comprueban consentimiento, lista autorizada y cita activa.
  Un recordatorio de 72h pendiente se descarta como `superseded` si ya corresponde 24h.
- `accepted` significa que Meta aceptó la petición. `sent`, `delivered`, `read` y
  `failed` provienen de sus notificaciones; no se presume entrega por un HTTP 200.
- Solo los errores explícitamente transitorios o HTTP 429 se reintentan, hasta
  tres intentos totales con espera de 2 y 4 minutos.
- Un timeout o una interrupción después de comenzar el envío queda `uncertain`.
  No se reenvía automáticamente: revisar en Meta antes de decidir un nuevo envío.
- Los acuses de texto se limitan a las 24 horas desde el mensaje del paciente.

Para demostrar 72h/24h sin esperar tres días, usar las pruebas con reloj controlado;
no cambiar el reloj de Windows ni alterar una base con procesos activos.

### Recordatorios con botones Confirmar / Cancelar

La nueva plantilla está definida en
[`database/plantilla_recordatorio_botones.json`](database/plantilla_recordatorio_botones.json):
`recordatorio_cita_botones_demo`, categoría Utilidad e idioma `es_CL`.
Tiene tres variables de cuerpo (profesional/especialidad, fecha y hora) y dos
botones de respuesta rápida: **Confirmar** y **Cancelar**. No muestra referencias
internas al paciente. Fue enviada a Meta el 18/11/2026 y quedó `PENDING` en ese corte.

Cuando Meta confirme que está `APPROVED` y que coinciden su cuerpo y botones:

```dotenv
WA_REMINDER_TEMPLATE=recordatorio_cita_botones_demo
WA_TEMPLATE_LANGUAGE=es_CL
WA_REMINDER_BUTTONS=1
```

Reiniciar API y worker para cargar el código/configuración. Mantener el emisor de
prueba y los destinatarios autorizados. La plantilla anterior `recordatorio_cita_demo`
permanece disponible como respaldo con `WA_REMINDER_BUTTONS=0` y cuatro variables.
Los mensajes anteriores no adquieren botones: la prueba real requiere un nuevo
recordatorio, conservando la unicidad por cita/umbral y los historiales existentes.

Cada botón lleva un identificador firmado con WA_APP_SECRET que vincula acción,
envío, paciente y cita. El webhook valida ese vínculo, el contexto cuando viene
incluido, el consentimiento y la pertenencia/fecha de la cita. No decide por la
etiqueta visible ni elige la última cita. También registra intentos inválidos.
Cambiar el secreto de la aplicación invalida los botones firmados con el anterior.

Prueba de aceptación: con dos citas activas, pulsar Cancelar en el recordatorio de
una debe cancelar únicamente esa cita; Confirmar debe mantener intacta la otra.
Repetir un clic no debe duplicar cambios. Botones alterados, ajenos o de citas
pasadas no deben modificar la agenda. Estas situaciones están cubiertas por tests;
la prueba en teléfono del nuevo modo queda pendiente de aprobación/activación.

Se conservan las entradas de texto 1/2 y CONFIRMAR/CANCELAR. Escribir solo 2 con
varias citas sigue requiriendo contexto; pulsar el botón del recordatorio sí
identifica su cita sin escribir un ID ni usar Responder manualmente.

Referencia de formato:
[plantillas con respuestas rápidas de Meta](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/types/TemplateObject/).

## 7. Despliegue y número propio: pendientes externos

Evaluación documental al 12/11/2026:

| Alternativa | Decisión |
|---|---|
| Render gratuito | Descartado para SQLite persistente: disco efímero y suspensión por inactividad. |
| PythonAnywhere gratuito nuevo | No ofrece tarea programada por minuto; no cumple el worker requerido. |
| Oracle Always Free | Candidato por VM y almacenamiento; requiere cuenta, tarjeta para verificación y disponibilidad regional. Sin cuenta no se ha comprobado despliegue ni permanencia. |
| PC + túnel HTTPS | Ruta de desarrollo preparada; depende del PC encendido. No acredita despliegue académico. |

Fuentes: [Render](https://render.com/docs/free),
[PythonAnywhere](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/),
[Oracle](https://www.oracle.com/cloud/free/faq/).
No se contrató ni creó infraestructura. El despliegue gratuito permanece pendiente
por falta de una cuenta y un entorno que permitan verificar persistencia, HTTPS y
worker autónomo. No se afirma que no existan otras alternativas.

Para el número propio: confirmar acceso a SMS/llamada, elegibilidad, requisitos de
cuenta, plantillas y tarifas en Meta. La plataforma cobra ciertos mensajes según
categoría y mercado; no asumir gratuidad de recordatorios proactivos.
[Tarifas oficiales](https://whatsappbusiness.com/products/platform-pricing/).
Con la restricción vigente de gasto cero, conservar el número de prueba si hay
cualquier requisito de pago. El código bloquea los envíos con número propio.

## 8. Verificación y evidencia

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check --select E4,E7,E9,F .
Get-ChildItem -File -Filter *.py | ForEach-Object { .\.venv\Scripts\python.exe -m py_compile $_.FullName }
```

Las pruebas usan bases temporales y HTTP simulado; no llaman a Meta. Registrar por
separado: pruebas automatizadas, capturas de teléfono sin secretos, estados del
panel y validación de reinicio/persistencia en nube. En el modo anterior se verificaron
confirmación, cancelación, acuses y recordatorios 72/24h entregados con el emisor de
prueba. Quedan pendientes el nuevo modo de botones en teléfono, el número propio
y el despliegue persistente. No equiparar tests simulados con entrega real.

La etiqueta `v0.2.0` identifica la versión del prototipo validada en local.
Las versiones siguen el flujo `feature → beta → master → etiqueta`.
