INSERT INTO patients (id, name, phone, email, consent_whatsapp)
VALUES
    (1, 'Paciente Demo Uno', '+56900000001', 'demo1@example.invalid', 0),
    (2, 'Paciente Demo Dos', '+56900000002', 'demo2@example.invalid', 0),
    (3, 'Paciente Demo Tres', '+56900000003', NULL, 0);

INSERT INTO professionals (id, name, active)
VALUES
    (1, 'Dra. Ana Martínez', 1),
    (2, 'Dr. Pablo Soto', 1),
    (3, 'Profesional Inactivo Demo', 0);

INSERT INTO specialties (id, name, active)
VALUES
    (1, 'Medicina General', 1),
    (2, 'Pediatría', 1),
    (3, 'Especialidad Inactiva Demo', 0);
