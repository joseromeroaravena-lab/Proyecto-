import os
import re
from dataclasses import dataclass, field

from whatsapp_servicio import normalizar_telefono


@dataclass
class Config:
    version: str = field(default_factory=lambda: os.getenv("WA_API_VERSION", ""))
    phone_id: str = field(default_factory=lambda: os.getenv("WA_PHONE_NUMBER_ID", ""))
    token: str = field(default_factory=lambda: os.getenv("WA_ACCESS_TOKEN", ""))
    secret: str = field(default_factory=lambda: os.getenv("WA_APP_SECRET", ""))
    verify: str = field(default_factory=lambda: os.getenv("WA_VERIFY_TOKEN", ""))
    enabled: bool = field(default_factory=lambda: os.getenv("WA_SEND_ENABLED") == "1")
    test_confirmed: bool = field(
        default_factory=lambda: os.getenv("WA_TEST_NUMBER_CONFIRMED") == "1"
    )
    allowed: set = field(
        default_factory=lambda: {
            normalizar_telefono(p.strip())
            for p in os.getenv("WA_ALLOWED_RECIPIENTS", "").split(",")
            if normalizar_telefono(p.strip())
        }
    )
    template: str = field(default_factory=lambda: os.getenv("WA_REMINDER_TEMPLATE", ""))
    language: str = field(
        default_factory=lambda: os.getenv("WA_TEMPLATE_LANGUAGE", "es")
    )
    buttons: bool = field(
        default_factory=lambda: os.getenv("WA_REMINDER_BUTTONS") == "1"
    )

    def validar_envio(self):
        # Sin presupuesto: ningún envío desde un número propio habilitado.
        if not self.enabled or not self.test_confirmed:
            raise ValueError(
                "Envíos bloqueados: habilitar solo el número de prueba de Meta."
            )
        if (
            not re.fullmatch(r"v[0-9]+\.[0-9]+", self.version)
            or not self.phone_id.isdigit()
            or not self.token
            or not self.allowed
        ):
            raise ValueError("Configuración de envío incompleta.")
        if self.buttons and not self.secret:
            raise ValueError(
                "Los botones requieren WA_APP_SECRET para vincular cada cita."
            )
