# Changelog

Registro de funcionalidades incorporadas y pendientes del prototipo CESFAM
Bellavista. Este documento refleja el código y la documentación revisados al
10/11/2026; una funcionalidad descrita como parcial o pendiente no debe
considerarse terminada ni desplegada.

## [En desarrollo] — 10/11/2026

### Incorporado

- **F1 — Agenda y panel:** existe una interfaz administrativa en Streamlit para
  consultar citas y sus estados, registrar pacientes ficticios y crear citas
  asociando paciente, profesional y especialidad. Se rechazan fechas pasadas y
  horarios ocupados para el mismo profesional.
- **F1 — Consultas locales:** hay scripts para consultar pacientes y citas, y
  un módulo de conexión a SQLite.
- **F2 — Simulación de respuesta:** `simular_respuesta.py` permite elegir
  confirmar o cancelar e ingresar una cita. La operación actualiza el estado
  si la cita futura pertenece al paciente indicado y está en un estado
  elegible, y registra la respuesta en `appointment_responses`.
- **Pruebas iniciales:** se agregaron pruebas automatizadas para una
  confirmación y para rechazar una respuesta de un paciente distinto, usando
  una base de datos temporal.
- **Integración continua:** GitHub Actions ejecuta lint, pruebas y verificación
  de compilación con Python 3.12 en pull requests y pushes a `main`/`master`.
- **Documentación y configuración:** se agregaron README, reglas `.gitignore`
  y manifiestos de dependencias para ejecución y desarrollo.

### Parcial o pendiente de completar

- **F1:** faltan los filtros de agenda por fecha, profesional y estado
  establecidos en HU-01. La aplicación necesita una base SQLite con el esquema
  esperado; no se incluye aquí una base de demostración preparada y reproducible.
- **F1:** aunque el panel consulta profesionales y especialidades, falta
  verificar y documentar de forma reproducible el esquema y los datos de
  demostración. La guía y las historias registran decisiones de modelo de datos
  todavía pendientes.
- **F2:** la simulación no demuestra todavía el flujo completo de chatbot ni
  satisface todos los criterios de HU-03/HU-04. Por ejemplo, las respuestas
  repetidas para citas ya confirmadas o canceladas no se registran como
  resultado idempotente; el registro actual tampoco conserva todos los datos de
  respuesta solicitados en las historias.
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
- **Pruebas completas:** faltan pruebas de integración y aceptación para los
  criterios de HU-01 a HU-07, además de casos para los flujos y errores
  pendientes.

## Alcance y seguridad

- El proyecto es un prototipo académico y no una integración con sistemas
  reales del CESFAM.
- Usar exclusivamente datos ficticios o sintéticos; no publicar información
  personal, clínica, secretos ni credenciales.
- `Chatbot_/chatbot.db` ya estaba seguido por Git. Añadirlo a `.gitignore` no
  deja de seguirlo ni lo elimina del historial; revisar su contenido antes de
  publicar o desplegar el repositorio.
- F4 requiere una decisión administrativa manual. No se ofrece reagendamiento
  desde el chatbot ni reasignación automática.

## Referencias

- `GUIA_CONTINUIDAD_CESFAM.md`: alcance del MVP, estado técnico y plan de
  continuidad.
- `docs/HISTORIAS_USUARIO.md`: criterios de aceptación de HU-01 a HU-07.

