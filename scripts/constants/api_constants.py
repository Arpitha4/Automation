from scripts.constants import EnvironmentConstants


class BaseURLPaths:
    step_module = '/workflow-mt/step'
    auth_endpoint = f'{EnvironmentConstants.base_path}{EnvironmentConstants.auth_endpoint}?project_id={EnvironmentConstants.project_id}'
    workflow = '/workflow-mt'
    workflow_module = f'{workflow}/workflow'
    ilens_module = '/ilens_api/ilens_config'
    hierarchy_module = '/hry/hierarchy'
    parameters = '/hry/parameters'


class ParametersAPI:
    save_parameter_category = f'{BaseURLPaths.parameters}/save_parameter_category'
    content_parameter_category = f'{BaseURLPaths.parameters}/get_parameter_category_content'
    save_parameter_groups = f'{BaseURLPaths.parameters}/save_params_for_parameter_group'
    get_parameter_group_content = f'{BaseURLPaths.parameters}/get_parameter_group_content'
    list_parameter_category = f'{BaseURLPaths.ilens_module}/list_tag_category'
    save_parameter = f'{BaseURLPaths.parameters}/save_parameters'
    get_parameter_content = f'{BaseURLPaths.parameters}/get_parameter_content'
    get_tag_types = f'{BaseURLPaths.ilens_module}/get_tag_types'
    get_data_types = f'{BaseURLPaths.ilens_module}/get_data_types'
    get_unit_data = f'{BaseURLPaths.ilens_module}/get_units'
    get_tag_groups = f'{BaseURLPaths.ilens_module}/get_tag_group'
