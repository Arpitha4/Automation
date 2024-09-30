from scripts.config.app_configurations import EnvironmentDetails


class AppConstants:
    step_category = 'step_category'
    project_type = 'project_type'
    tz = 'tz'
    langauge = 'language'
    metadata_sheet = 'Metadata'
    permissions = 'Permissions'
    actions = 'Actions'
    approval = 'Approval'
    parameter_category = 'parameter category'
    parameter_groups = 'parameter group'
    parameter = 'parameter'
    unit_sheet = 'unit'
    unit_groups_sheet = 'unit group'


class AutomationConstants:
    tz = 'Asia/Kolkata'
    language = 'en'
    project_type = 'n_level_hierarchy'
    delimiter_symbol = '=>'
    bool_map = {
        'true': True,
        'false': False
    }
    encrypt_payload = bool_map.get(EnvironmentDetails.encrypt_payload.lower(), False)


class Secrets:
    LOCK_OUT_TIME_MINS = 30
    leeway_in_mins = 10
    unique_key = "45c37939-0f75"
    token = "8674cd1d-2578-4a62-8ab7-d3ee5f9a"
    issuer = "ilens"
    alg = "HS256"
    signature_key = "kliLensKLiLensKL"
    signature_key_alg = ["HS256"]
    headers = {
        'Content-Type': 'application/json',
    }
    secret_key = '9b7aa294-d803-4fc1-8c99-6bff666e9635'
