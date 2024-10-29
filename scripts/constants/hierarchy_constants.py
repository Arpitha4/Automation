from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class HierarchyConstants:
    payload_data = {
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }

    hierarchy_meta_data = {
        "hierarchy": "name",
        "parameter name": "tags"
    }

    hierarchy_save_payload = {
        "inside_site_conf": False,
        "type": "",
        "condition": {},
        "data": [
            {
                "node_id": "",
                "name": "",
                "parent_id": "",
                "project_id": EnvironmentConstants.project_id,
                "type": "",
                "description": "",
                "tags": []
            }
        ],
        "node_id": "",
        "parent_id": "",
        "node_name": "",
        "customer_project_id": EnvironmentConstants.project_id,
        "project_id": EnvironmentConstants.project_id,
        "project_type": AutomationConstants.project_type,
        "tz": EnvironmentConstants.tz,
        "language": AutomationConstants.language
    }
