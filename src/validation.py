class ValidationError(ValueError):
    """Raised when a flight does not meet operational eligibility rules."""


class FlightValidator:
    def validate(self, aircraft, total_weight_kg: float) -> None:
        if aircraft["maintenance_status"] != "LIBERADO":
            raise ValidationError("Aeronave não está liberada para operação.")
        if total_weight_kg > aircraft["useful_load_kg"]:
            raise ValidationError("Peso total excede a capacidade útil da aeronave.")
        if total_weight_kg <= 0:
            raise ValidationError("O peso total deve ser maior que zero.")