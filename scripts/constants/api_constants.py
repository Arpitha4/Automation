from scripts.constants import EnvironmentConstants


class BaseURLPaths:
    auth_endpoint = f'{EnvironmentConstants.base_path}{EnvironmentConstants.auth_endpoint}?project_id={EnvironmentConstants.project_id}'
    ilens_module = '/ilens_api/ilens_config'
    hierarchy_module = '/hry/hierarchy'
    parameters = '/hry/parameters'
    units = '/hry/units'
    hierarchy = '/hry/hry/'
    asset_model = '/scada_dt/asset'
    industry = '/ilens_api/industry'


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


class UnitAPI:
    list_unit_groups_data = f'{BaseURLPaths.units}/list_unit_groups'
    save_unit_groups = f'{BaseURLPaths.ilens_module}/save_unit_group'
    list_units_data = f'{BaseURLPaths.units}/list_units'
    get_units_data = f'{BaseURLPaths.units}/get_unit_groups'
    save_units = f'{BaseURLPaths.units}/save_units'


class HierarchyAPI:
    fetch_hierarchy = f'{BaseURLPaths.hierarchy}/fetch_accessible_data'
    save_hierarchy = f'{BaseURLPaths.hierarchy_module}/save'


class AssetModelAPI:
    asset_model_list = f'{BaseURLPaths.asset_model}/list'
    save_asset_model = f'{BaseURLPaths.asset_model}/save'
    drop_down_list = f'{BaseURLPaths.industry}/list_dropdown'
    asset_tag = f'{BaseURLPaths.ilens_module}/asset_tag_group'
    asset_tag_meta = f'{BaseURLPaths.ilens_module}/asset_tag_group_meta'
    add_delete_param = f'{BaseURLPaths.asset_model}/add_delete_param'
    create_drop_down = f'{BaseURLPaths.industry}/create'

