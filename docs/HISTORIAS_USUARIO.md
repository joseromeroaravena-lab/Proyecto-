# Historias de usuario — CESFAM Bellavista

Fecha: 18/10/2026. Entregable propuesto para Sumativa 1 (27/10/2026).
Fuente de alcance: GUIA_CONTINUIDAD_CESFAM.md. Pendiente de validación con el docente.
Estas historias describen requisitos; no acreditan funcionalidades implementadas o probadas.
Todos los escenarios usan datos ficticios o sintéticos.

## HU-01 — Consultar agenda (F1)

**Como** administrativo/a, **quiero** consultar pacientes, profesionales y citas en un panel, **para** conocer la agenda y sus estados.

Prioridad: alta. Entrega funcional: Sumativa 2, 24/11/2026.

- Dado que existen citas ficticias, cuando abro la agenda, entonces veo identificador de cita, paciente, profesional, especialidad, fecha, hora y estado.
- Dado que consulto la agenda, cuando filtro por fecha, profesional o estado, entonces solo se muestran las citas coincidentes.
- Dado que ningún registro coincide con los filtros, cuando consulto, entonces el panel informa que no hay resultados.

## HU-02 — Registrar una cita (F1)

**Como** administrativo/a, **quiero** registrar una cita asociada a un paciente y un profesional, **para** mantener una agenda simulada.

Prioridad: alta. Entrega funcional: Sumativa 2, 24/11/2026.

- Dado un paciente y un profesional existentes, cuando registro especialidad, fecha y hora válidas, entonces se guarda una cita con estado inicial pendiente (`scheduled`).
- Dado que falta un dato obligatorio o el paciente o profesional no existe, cuando intento registrar la cita, entonces se rechaza y se explica el dato que debo corregir.
- Dado que el profesional ya tiene una cita activa en esa fecha y hora, cuando intento ocupar el mismo horario, entonces se rechaza la segunda asignación.

Decisión de diseño pendiente: normalizar profesionales en su propia tabla para cumplir la gestión de profesionales de F1.

## HU-03 — Confirmar una cita (F2)

**Como** paciente, **quiero** confirmar mi cita mediante el chatbot de prueba, **para** informar mi intención de asistir.

Prioridad: alta. Entrega funcional: Sumativa 2, 24/11/2026. Depende de F1.

- Dada una cita pendiente asociada a mi conversación de prueba, cuando respondo CONFIRMAR, entonces pasa a confirmada y recibo un acuse de recibo.
- Dada una respuesta recibida, cuando se procesa, entonces se conserva su cita, paciente, fecha, contenido y resultado.
- Dada una cita ya confirmada, cuando repito CONFIRMAR, entonces permanece confirmada y se registra el resultado sin duplicar la cita.

## HU-04 — Cancelar una cita (F2)

**Como** paciente, **quiero** cancelar mi cita mediante el chatbot de prueba, **para** avisar que no asistiré.

Prioridad: alta. Entrega funcional: Sumativa 2, 24/11/2026. Depende de F1.

- Dada una cita pendiente o confirmada, cuando respondo CANCELAR, entonces se marca cancelada, se conserva la cita y recibo la confirmación.
- Dada una cancelación recibida, cuando se procesa, entonces se registra la respuesta con fecha y resultado.
- Dada una cita cancelada, cuando repito CANCELAR, entonces permanece cancelada y se informa su estado actual.
- Dada una entrada diferente de CONFIRMAR o CANCELAR, cuando el chatbot la recibe, entonces explica las opciones y no modifica el estado de la cita.

El chatbot no ofrece reagendamiento. La alerta y reasignación manual se incorporan en F4.

## HU-05 — Recibir recordatorios (F3)

**Como** paciente, **quiero** recibir recordatorios 72 y 24 horas antes de mi cita, **para** recordar la atención y responder si asistiré.

Prioridad: alta. Entrega funcional: Sumativa 2, 24/11/2026. Depende de F1 y del canal de prueba.

- Dada una cita activa creada con anticipación suficiente, cuando el reloj de prueba alcanza los umbrales de 72 y 24 horas, entonces se genera el recordatorio correspondiente a cada umbral.
- Dado un recordatorio ya generado para una cita y un umbral, cuando se ejecuta nuevamente el proceso, entonces no se genera un duplicado.
- Dada una cita cancelada, cuando se evalúan recordatorios pendientes, entonces no se envían nuevos recordatorios para esa cita.
- Dado un envío exitoso o fallido, cuando finaliza el intento, entonces se registra su tipo, fecha y estado consultable en el panel.

Pendiente de acordar: frecuencia de ejecución, tratamiento de citas creadas después de un umbral y política de reintentos. Las pruebas deben controlar el reloj y la zona horaria America/Santiago.

## HU-06 — Reasignar manualmente un cupo (F4)

**Como** administrativo/a, **quiero** recibir una alerta al liberarse un cupo y seleccionar una persona de la lista de espera, **para** reasignar la atención mediante una decisión manual.

Prioridad: media. Entrega funcional: Sumativa 3, 15/12/2026. Depende de F1 y F2.

- Dada una cita activa, cuando el paciente la cancela, entonces el horario queda disponible y aparece una alerta administrativa vinculada a la cancelación.
- Dado un cupo libre, cuando consulto la lista de espera, entonces veo pacientes ficticios que esperan la especialidad correspondiente y su prioridad.
- Dado un paciente elegible diferente del titular original, cuando selecciono y confirmo manualmente la reasignación, entonces se reserva el cupo, se actualiza la lista y se registra la decisión con fecha y responsable.
- Dadas dos operaciones que intentan ocupar el mismo cupo, cuando se confirman, entonces solo una puede completarse.
- Dada una cancelación y su posterior reasignación, cuando consulto el historial, entonces se conserva la relación entre ambas operaciones.

No se seleccionan pacientes ni se envían ofertas de reasignación automáticamente.

## HU-07 — Consultar riesgo simulado de inasistencia (F5)

**Como** administrativo/a, **quiero** consultar un indicador de riesgo por paciente, **para** explorar la priorización de seguimiento en la demostración académica.

Prioridad: media. Entrega funcional: Sumativa 3, 15/12/2026.

- Dado un modelo sencillo entrenado con datos sintéticos, cuando calculo un indicador, entonces se guarda su valor, fecha de cálculo y versión del modelo.
- Dado un indicador disponible, cuando consulto el panel, entonces se muestra por paciente y se identifica claramente como resultado simulado.
- Dado un paciente sin cálculo disponible, cuando consulto su indicador, entonces se informa que no hay resultado en lugar de asignar un riesgo ficticio por defecto.
- Dado un entrenamiento, cuando reviso su documentación, entonces encuentro procedencia sintética de datos, variables, separación de entrenamiento y evaluación, y métricas obtenidas.

Pendiente de acordar: variables, métrica de evaluación y umbrales de presentación. El indicador no acredita una reducción real de inasistencias.

## Trazabilidad y estado

| Función | Historias | Estado verificado al 18/10/2026 |
|---|---|---|
| F1 | HU-01, HU-02 | Scripts de consulta y creación presentes; SQLite contiene una cita. Panel y tabla de profesionales pendientes. |
| F2 | HU-03, HU-04 | No se identificó implementación en los archivos inspeccionados. |
| F3 | HU-05 | No se identificó implementación en los archivos inspeccionados. |
| F4 | HU-06 | Existen tablas de espera y ofertas; no acreditan alertas ni reasignación manual implementadas. |
| F5 | HU-07 | No se identificó implementación en los archivos inspeccionados. |

## Observaciones del workspace

- El repositorio local tiene remoto origin configurado en GitHub; no se verificó el estado del servidor ni se realizó un push.
- Chatbot_/chatbot.db ya figura entre los archivos seguidos por Git. Agregar un .gitignore no elimina ese seguimiento ni los datos del historial. Revisar antes de publicar.
- El esquema real exige especialidad, profesional y fecha en appointments. outbox.message permite NULL; corregir esa diferencia en el futuro diccionario de datos.
- La inspección de SQLite se realizó en modo de solo lectura. No se ejecutó crear_cita.py ni se modificaron registros.
