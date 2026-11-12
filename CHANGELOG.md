# Changelog

Registro de funcionalidades incorporadas y pendientes del prototipo CESFAM
Bellavista. Este documento refleja el código y la documentación revisados al
12/11/2026; una funcionalidad descrita como parcial o pendiente no debe
considerarse terminada ni desplegada.

## [En desarrollo]

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
  de compilación con Python 3.12 en pull requests y pushes a `main`/`master`.
- **Documentación y configuración:** se agregaron README, reglas `.gitignore`
  y manifiestos de dependencias para ejecución y desarrollo.

### Parcial o pendiente de completar

- **F1:** faltan los filtros de agenda por fecha, profesional y estado. El
  inicializador ya permite preparar una base reproducible, pero quedan decisiones
  del modelo de datos y pruebas del panel por completar.
- **F2:** la simulación no demuestra todavía el flujo completo de chatbot ni
  todos los flujos esperados. Por ejemplo, las respuestas repetidas para citas
  ya confirmadas o canceladas no se registran como resultado idempotente; el
  registro actual tampoco conserva todos los datos de respuesta previstos.
- **Despliegue:** no se ha desplegado la aplicación. Streamlit Community Cloud
  está documentado como destino posible, pero antes hay que resolver la
  provisión y persistencia de SQLite y preparar datos exclusivamente ficticios.

### Aún no implementado

- **F3 — Recordatorios:** generación y registro de recordatorios a 72 y 24 horas,
  prevención de duplicados, control de zona horaria y registro de intentos
  exitosos o fallidos.
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

[En desarrollo]: https://github.com/joseromeroaravena-lab/Proyecto-/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/joseromeroaravena-lab/Proyecto-/releases/tag/v0.1.0

