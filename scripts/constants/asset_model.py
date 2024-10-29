from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class AssetModelConstants:
    asset_model_content_json = {
        "filters": {},
        "records": 50,
        "counter": 1,
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    asset_model_filters = {
        "showFiltersSidebar": "",
        "search": ""
    }

    asset_model_metadata = {
        "asset model name": "asset_model_name",
        "description": "description",
        "industry": "industry",
        "select type": "select_type",
        "parameter group/parameter category": "parameter_groups/parameter_category",
        "increment version": "increment_version"
    }

    asset_model_creation_json = {
        "key_type": "",
        "data": {},
        "asset_model_id": "",
        "asset_version": "",
        "asset_model_name": "",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    drop_down_data = {
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    create_drop_down = {
        "industry_category_name": "",
        "description": "",
        "industry_category_id": "",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    tag_data = {
        "type": "",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    add_parameter = {
        "parameter_id": [
        ],
        "asset_model_id": "",
        "asset_version": "",
        "action": "add_only",
        "node_ids": [],
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }
