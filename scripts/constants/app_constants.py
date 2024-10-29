from scripts.config.app_configurations import EnvironmentDetails


class AppConstants:
    parameter_category = 'parameter category'
    parameter_groups = 'parameter group'
    parameter = 'parameter'
    unit_sheet = 'unit'
    unit_groups_sheet = 'unit group'
    hierarchy = 'hierarchy'
    asset_model = 'asset model'
    industry = 'industry'


class AutomationConstants:
    language = 'en'
    project_type = 'n_level_hierarchy'
    bool_map = {
        'true': True,
        'false': False
    }
    encrypt_payload = bool_map.get(EnvironmentDetails.encrypt_payload.lower(), False)


class Secrets:
    LOCK_OUT_TIME_MINS = 30
    issuer = "ilens"
    alg = "HS256"
    signature_key = "kliLensKLiLensKL"
    headers = {
        'Content-Type': 'application/json',
    }
