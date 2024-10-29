from scripts.constants import EnvironmentConstants
from scripts.constants.app_constants import AutomationConstants


class IndustryConstants:
    industry_meta_data = {
        "industry name": "industry",
        "description": "description"
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
