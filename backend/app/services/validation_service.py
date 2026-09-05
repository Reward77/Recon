from app.core.canonical_schema import CANONICAL_SCHEMA

class ValidationService:

    @staticmethod
    def validate_columns(df):

        missing = []

        for field in CANONICAL_SCHEMA.values():
            if field.required and field.name not in df.columns:
                missing.append(field.name)

        if missing:
            raise Exception(
                f"Missing required columns: {', '.join(missing)}"
            )

        return True