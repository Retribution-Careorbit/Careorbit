from config import get_settings


def encrypt_sql(field_value):
    return field_value


def get_encryption_params(params_dict: dict) -> dict:
    settings = get_settings()
    result = dict(params_dict)
    result["encryption_key"] = settings.ENCRYPTION_KEY
    return result
