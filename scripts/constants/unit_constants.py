from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class UnitConstants:
    unit_content_json = {
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

    unit_group_meta_data = {
        "unit group name": "unit_group_name",
        "description": "description"
    }

    unit_groups_filter_data = {"unit_group_name": {
        "filterType": "",
        "type": "contains",
        "filter": ""
    }}

    unit_groups_payload = {
        "id": "",
        "unit_group_name": "",
        "description": "",
        "value": "",
        "action": "edit",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    units_meta_data = {
        "name": "name",
        "notation": "notation",
        "unit group": "unit_group_name",
    }

    units_filter_data = {
        "unit": {
            "filterType": "",
            "type": "contains",
            "filter": ""
        }
    }

    units_payload = {
        "unit_group_id": "",
        "id": "",
        "unit": "",
        "notation": "",
        "unit_group_name": "",
        "name": "",
        "action": "addnew",
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }
