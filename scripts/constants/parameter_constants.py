from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class ParameterConstants:
    parameter_content_json = {
        "startRow": 0,
        "endRow": 100,
        "page": 1,
        "records": 100,
        "filters": {
            "sortModel": [],
            "filterModel": {}
        },
        "global_filters": {},
        "metaData": {},
        "tag_fetch_type": "",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    parameter_category_filter_model = {"tag_category_name": {
        "filterType": "text",
        "type": "contains",
        "filter": "test_1"
    }}

    parameter_json = {
        "tag_name": "",
        "unit": None,
        "tag_type": None,
        "description": "",
        "tag_id": "",
        "tag_group_id": "",
        "data_type": None,
        "value_list": [],
        "system_tag_type": "raw_tag",
        "tag_category_id": None,
        "data_quality_info": {
            "basic": {
                "value": None,
                "required": False
            },
            "numeric_limit": {
                "min": None,
                "max": None
            },
            "string_length": {
                "min": None,
                "max": None
            }
        },
        "tag_label": None,
        "unit_name": "",
        "tag_type_name": "",
        "system_tag_label": "",
        "tag_group_name": "",
        "data_type_name": "",
        "parameter_category": "",
        "id": "",
        "default": False,
        "type": "edit",
        "additional_fields": {},
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    meta_data_mapping = {
        "parameter name": "tag_name",
        "description": "description",
        "data source": "system_tag_label",
        "data type": "tag_type_name",
        "ui input type": "tag_type",
        "parameter label": "tag_label",
        "unit": "unit_name",
        "parameter group": "tag_group_name",
        "parameter category": "parameter_category",
        "numeric limit": "numeric_limit",
        "string length": "string_length",
        "default value": "basic",
        "input required": "required"
    }

    parameter_filter_model = {"tag_name": {
        "filterType": "text",
        "type": "contains",
        "filter": ""
    }}

    parameter_category_meta_data = {
        "parameter category name": "tag_category_name",
        "description": "description",
        "icon": "tag_category_icon"
    }

    parameter_category_json = {
        "tag_category_name": "",
        "description": "",
        "tag_category_icon": "",
        "tag_category_id": "",
        "tagsList": [],
        "deletedTags": [],
        "type": "",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    parameter_groups_meta_data = {
        "parameter group name": "tag_group_name",
        "description": "description",
        "parameter category": "category"
    }

    parameter_groups_json = {
        "tag_group_id": "",
        "tag_group_name": "Volume",
        "description": "Volume",
        "category": "",
        "selectedTags": [],
        "deletedTags": [],
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }
    parameter_groups_filter_model = {"tag_group_name": {
        "filterType": "text",
        "type": "contains",
        "filter": ""
    }}

    list_parameter_category = {
        "lookup_name": "tag_categories",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }
