from scripts.constants import EnvironmentConstants


class BaseURLPaths:
    get_parameter_content = 'hry/parameters/get_parameter_content'
    ilens_module = '/ilens_api/ilens_config'
    hierarchy_module = '/hry/hierarchy'
    auth_endpoint = f'{EnvironmentConstants.base_path}{EnvironmentConstants.auth_endpoint}?project_id={EnvironmentConstants.project_id}'


