# Changelog

Registro del estado del prototipo CESFAM Bellavista, revisado el 22/11/2026.

## [0.2.0] — 2026-11-22

### Instalación local

- Plantilla `.env.example` con las variables vacías. Para abrir el panel, copiar
  la plantilla a `.env` y definir `CESFAM_PANEL_PASSWORD`.
- El panel usa `chatbot.db` cuando `CESFAM_DB_PATH` queda vacía. Los envíos de
  WhatsApp permanecen desactivados en la configuración inicial.

### Filtros de agenda

- Filtros combinables por fecha, profesional y estado, con opción Limpiar filtros.
- Actualizar agenda conserva la selección y muestra los estados vigentes, con
  contadores de citas encontradas y citas registradas.
- La fecha incluye todo el día. Las opciones de profesional incluyen registros
  históricos e inactivos presentes en las citas.
- Pruebas de consulta e interfaz para los filtros, los casos sin coincidencias
  y la actualización de estados en el panel con acceso administrativo.

### Botones por cita

- Nuevo modo opcional de plantilla con Confirmar/Cancelar, tres variables de cuerpo
  y vínculo firmado de cada botón con envío, paciente, cita y acción.
- Soporte de respuestas de plantilla e interactivas; protección ante botones
  alterados, ajenos o de citas pasadas, y acuses con profesional/fecha/hora.
- Compatibilidad con la plantilla anterior y comandos de texto. No se selecciona
  automáticamente una cita si una respuesta numérica es ambigua.
- La plantilla se envió a Meta el 18/11/2026 y quedó en estado `PENDING` en esa
  revisión. La prueba con botones en el teléfono sigue pendiente.

### Integración de WhatsApp para pruebas locales

- Webhook firmado, respuestas idempotentes y worker de recordatorios implementados.
- Migración con respaldo, acceso al panel y consulta de actividad.
- Envíos apagados por defecto; solo se permite el emisor de prueba de Meta.
- Instrucciones en WHATSAPP.md; configuración Meta y despliegue pendientes.

### Incorporado

- **F1 — Agenda y panel:** existe una interfaz administrativa en Streamlit para
  consultar citas y sus estados, registrar pacientes ficticios y crear citas
  asociando paciente, profesional y especialidad. Se rechazan fechas pasadas y
  horarios ocupados para el mismo profesional.
- **F2 — Simulación de respuesta:** `simular_respuesta.py` permite elegir
  confirmar o cancelar e ingresar una cita. La operación actualiza el estado
  si la cita futura pertenece al paciente indicado y está en un estado
  elegible, y registra la respuesta en `appointment_responses`.
- **Pruebas iniciales:** se agregaron pruebas automatizadas para una
  confirmación y para rechazar una respuesta de un paciente distinto, usando
  una base de datos temporal.
- **Base reproducible:** `crear_base.py` genera una SQLite completa a partir de
  `database/schema.sql` y `database/seed_demo.sql`. Incluye catálogos, pacientes
  y citas ficticias relativas a la fecha de instalación; conserva cualquier
  base existente y valida integridad y claves foráneas.
- **Pruebas del inicializador:** se comprueba la creación completa, la
  conservación de una base existente y la limpieza si el esquema falla.
- **Integración continua:** GitHub Actions ejecuta lint, pruebas y verificación
  de compilación con Python 3.12 en pull requests y pushes a `beta`, `main` o
  `master`.
- **Documentación y configuración:** se agregaron README, reglas `.gitignore`
  y manifiestos de dependencias para ejecución y desarrollo.

### Parcial o pendiente de completar

- **F1:** filtros implementados y cubiertos por pruebas de consulta e interfaz.
  Queda revisar visualmente el resultado y completar la aceptación de la función.
- **F2:** el flujo con botones está verificado con HTTP simulado. Falta
  comprobar el nuevo modo en un teléfono autorizado.
- **F3:** generación local de recordatorios de 72 y 24 horas, prevención de
  duplicados, control de zona horaria y registro de intentos. Queda pendiente
  validar la entrega con la nueva plantilla.
- **Despliegue:** no se ha desplegado la aplicación. La evaluación está en
  WHATSAPP.md; falta comprobar un entorno gratuito con persistencia y worker.

### Aún no implementado

- **F4 — Reasignación manual:** alerta administrativa al liberarse una cita,
  selección manual desde la lista de espera, reserva transaccional e historial
  de la reasignación. La existencia de tablas `waitlist` u `offers` no acredita
  esta funcionalidad; no se debe implementar una reasignación automática como
  sustituto.
- **F5 — Riesgo simulado:** entrenamiento con datos sintéticos, cálculo y
  almacenamiento de indicadores con fecha y versión del modelo, visualización
  claramente simulada y documentación de evaluación.
- **Pruebas completas:** faltan pruebas de integración y aceptación del panel,
  además de casos para los flujos y errores pendientes.

## [0.1.0] — 2026-10-27

Primera versión correspondiente a la Sumativa 1, etiquetada retrospectivamente
sobre el commit `21a560f` del 18/10/2026.

### Incorporado

- Conexión inicial entre Python y una base SQLite local.
- Script para registrar una cita ficticia.
- Scripts de consola para consultar pacientes y citas.
- Primera base de demostración utilizada durante el desarrollo inicial de F1.

Esta versión todavía no incluía el panel Streamlit, la simulación de respuestas,
las pruebas automatizadas ni la integración continua.

## Alcance y seguridad

- El proyecto es un prototipo académico y no una integración con sistemas
  reales del CESFAM.
- Usar exclusivamente datos ficticios o sintéticos; no publicar información
  personal, clínica, secretos ni credenciales.
- Una versión anterior de `Chatbot_/chatbot.db` permanece en el historial de
  Git aunque el archivo actual esté ignorado; revisar ese historial antes de
  publicar o desplegar el repositorio.
- F4 requiere una decisión administrativa manual. No se ofrece reagendamiento
  desde el chatbot ni reasignación automática.

## Referencias

- `README.md`: instalación, ejecución, CI y despliegue previsto.

La guía de continuidad, las historias de usuario y los documentos de
planificación se conservan fuera del repositorio y no se enlazan desde GitHub.

[0.2.0]: https://github.com/joseromeroaravena-lab/Proyecto-/tree/v0.2.0
[0.1.0]: https://github.com/joseromeroaravena-lab/Proyecto-/releases/tag/v0.1.0
