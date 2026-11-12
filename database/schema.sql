CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT,
    consent_whatsapp INTEGER NOT NULL DEFAULT 0
        CHECK (consent_whatsapp IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE professionals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE specialties (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    specialty TEXT NOT NULL,
    professional TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'confirmed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    professional_id INTEGER REFERENCES professionals(id),
    specialty_id INTEGER REFERENCES specialties(id)
);

CREATE TABLE appointment_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
    response TEXT NOT NULL CHECK (response IN ('confirmar', 'cancelar')),
    channel TEXT NOT NULL,
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    appointment_id INTEGER REFERENCES appointments(id),
    message TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TEXT
);

CREATE TABLE waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    specialty TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'waiting',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    status TEXT NOT NULL DEFAULT 'pending',
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_date
    ON appointments (appointment_date);

CREATE INDEX idx_appointments_patient
    ON appointments (patient_id);

CREATE INDEX idx_appointments_professional_date
    ON appointments (professional_id, appointment_date);
