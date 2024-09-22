from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class ParameterConstants:
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
