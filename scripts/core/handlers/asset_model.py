import copy
import pandas as pd
import openpyxl
import requests

from fastapi import HTTPException

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import AssetModelAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.asset_model import AssetModelConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class AssetModelHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None,
                 response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages or ""
        self.asset_metadata = dict()
        self.asset_list = []

    def automate_asset_model(self):
        try:
            logger.info("Initiated Asset Model automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.asset_model)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_asset_data(merged_row_groups, df)
            self.convert_asset_metadata_to_dict(df)
            _, asset_model_data = self.check_asset_model_exits()
            existing_asset_model = [asset["asset_model_name"].lower() for asset in asset_model_data]
            new_asset_model = [asset["asset_model_name"].lower() for asset in self.asset_list]
            added_model = []
            existing_model = []
            for new_tag in new_asset_model:
                if new_tag not in existing_asset_model:
                    added_model.append(new_tag)
            for existing_tag in existing_asset_model:
                if existing_tag not in new_asset_model:
                    existing_model.append(existing_tag)
            if added_model:
                logger.info("Initiated Asset Model Creation!!")
                for each_asset_model in self.asset_list:
                    if each_asset_model["asset_model_name"].lower() in added_model:
                        self.create_asset_model(each_asset_model=each_asset_model)
                msg = f"Created Asset Model: {added_model}\n"
                logger.info(msg)
                self.response_messages += msg
                if added_model:
                    logger.info(f"Added Asset Model: {', '.join(added_model)}")
                if existing_model:
                    logger.info(f"Existing Asset Model: {', '.join(existing_model)}")
            if existing_model:
                msg = f"Asset Model Information Exists: {existing_asset_model}\n"
                logger.info(msg)
                self.response_messages += msg
                for each_asset_model in self.asset_list:
                    if each_asset_model["asset_model_name"].lower() not in added_model:
                        logger.info(f"Adding next version of the asset model:{each_asset_model['asset_model_name'].lower()}")
                        self.add_next_version(each_asset_model=each_asset_model, existing_asset_model_data=asset_model_data)
            return self.response_messages
        except Exception as asset_error:
            msg = f"Error while automating asset model: {asset_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def extract_asset_data(self, merged_row_groups, df):
        try:
            group_dfs = []
            for each in merged_row_groups:
                try:
                    group_df = df.iloc[each].reset_index(drop=True)
                    group_df.dropna(how='all', inplace=True)
                    group_df.dropna(how='all', axis=1, inplace=True)
                    group_dfs.append(group_df)
                except Exception as group_error:
                    logger.error(f"Error processing merged row group {each}: {group_error}")
            if not group_dfs:
                logger.warning("No valid groups found after processing merged rows.")
                raise ValueError("No valid groups found.")
            result_df = pd.concat(group_dfs, ignore_index=True)
            return result_df
        except Exception as extraction_error:
            msg = f"Error while extracting asset model data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_asset_metadata_to_dict(self, df):
        try:
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[1]
            self.asset_list = []
            for row in range(2, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = AssetModelConstants.asset_model_metadata.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'asset_model_name':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Asset Model Name is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'description':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Asset Model Description is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'industry':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Asset Model industry is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.asset_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting Asset model metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_asset_model(self, each_asset_model):
        try:
            payload_data = copy.deepcopy(AssetModelConstants.asset_model_creation_json)

            asset_model_data = self.create_asset_model_basic_info(payload_data=payload_data,
                                                                  each_asset_model=each_asset_model)
            self.create_asset_model_parameters(payload_data=payload_data, each_asset_model=each_asset_model,
                                               asset_model_data=asset_model_data)
        except Exception as e:
            msg = f"Error while creating Asset model: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_asset_model_basic_info(self, payload_data, each_asset_model):
        try:
            payload_data["key_type"] = "basic_info"
            payload_data["asset_model_name"] = each_asset_model['asset_model_name']
            _, drop_down = self.get_drop_down_data(each_asset_model=each_asset_model)
            if drop_down:
                basic_info_data = {
                    "asset_model_name": each_asset_model['asset_model_name'],
                    "asset_description": each_asset_model['description'],
                    "description": "",
                    "industry": drop_down["industry_category_name"],
                    "industry_category_id": drop_down["industry_category_id"],
                    "thing_type_id": "",
                    "update_section": [],
                    "critical_parameters": [],
                    "asset_model_image": "",
                    "project_id": EnvironmentConstants.project_id,
                }
                payload_data["data"] = basic_info_data
                if each_asset_model["increment_version"].lower() == "yes":
                    payload_data["data"]["increment_version"] = True

                url = f'{EnvironmentConstants.base_path}{AssetModelAPI.save_asset_model}'
                try:
                    # encode payload into JWT
                    if self.encrypt_payload:
                        payload = JWT().encode(payload=payload_data)
                        response = requests.post(url, data=payload, headers=Secrets.headers, cookies=self.login_token)
                    else:
                        response = requests.post(url, json=payload_data, headers=Secrets.headers,
                                                 cookies=self.login_token)
                    if response.status_code != 200:
                        msg = "Failed to fetch asset model data\n"
                        logger.error(msg)
                        self.response_messages += msg
                        raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                    response = response.json()
                    response = response.get('data', {})
                except requests.RequestException as request_error:
                    logger.error(f"Request error during asset model creation: {request_error}")
                    raise HTTPException
                if response:
                    return response
            else:
                msg = f"Industry {each_asset_model['industry']} not found\n"
                logger.exception(msg)
                self.response_messages += msg
                raise ValueError(self.response_messages)
        except Exception as e:
            msg = f"Error while creating Asset model basic info: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_asset_model_parameters(self, payload_data, each_asset_model, asset_model_data):
        try:
            payload_data["key_type"] = "parameters"
            payload_data["asset_model_name"] = each_asset_model.get('asset_model_name', '')
            payload_data["asset_model_id"] = asset_model_data.get('asset_model_id', '')
            payload_data["asset_version"] = asset_model_data.get('asset_version', '')
            if each_asset_model["select_type"].lower() == "parameter group":
                tag_group = self.get_asset_tag_group(each_asset_model=each_asset_model)
                if tag_group[0]:
                    tags = self.get_tags_groups(tag_group=tag_group[1], each_asset_model=each_asset_model)
                    asset_model_parameters = {
                        "parameters": tags,
                        "asset_model_name": each_asset_model.get('asset_model_name', ''),
                        "critical_parameters": []
                    }
                    payload_data["data"] = asset_model_parameters
                    self.add_parameter(data=payload_data)
            if each_asset_model["select_type"].lower() == "parameter category":
                tag_category = self.get_asset_tag_category(each_asset_model=each_asset_model)
                if tag_category[0]:
                    tags = self.get_tags_category(tag_category=tag_category[1], each_asset_model=each_asset_model)
                    asset_model_parameters = {
                        "parameters": tags,
                        "asset_model_name": each_asset_model.get('asset_model_name', ''),
                        "critical_parameters": []
                    }
                    payload_data["data"] = asset_model_parameters
                    self.add_parameter(data=payload_data)

                    url = f'{EnvironmentConstants.base_path}{AssetModelAPI.save_asset_model}'
                    try:
                        # encode payload into JWT
                        if self.encrypt_payload:
                            payload = JWT().encode(payload=payload_data)
                            response = requests.post(url, data=payload, headers=Secrets.headers,
                                                     cookies=self.login_token)
                        else:
                            response = requests.post(url, json=payload_data, headers=Secrets.headers,
                                                     cookies=self.login_token)
                        if response.status_code != 200:
                            msg = "Failed to fetch asset model data\n"
                            logger.error(msg)
                            self.response_messages += msg
                            raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                    except requests.RequestException as request_error:
                        logger.error(f"Request error during asset model creation: {request_error}")
                        raise HTTPException
        except Exception as e:
            msg = f"Error while creating Asset model parameter: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def add_parameter(self, data):
        try:
            payload_data = copy.deepcopy(AssetModelConstants.add_parameter)
            payload_data["parameter_id"] = data.get('data', {}).get('parameters', [])
            payload_data["asset_model_id"] = data.get('asset_model_id', '')
            payload_data["asset_version"] = data.get('asset_version', '')
            try:
                url = f'{EnvironmentConstants.base_path}{AssetModelAPI.add_delete_param}'
                # encode payload into JWT
                if self.encrypt_payload:
                    payload = JWT().encode(payload=payload_data)
                    response = requests.post(url, data=payload, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload_data, headers=Secrets.headers,
                                             cookies=self.login_token)
                if response.status_code != 200:
                    msg = "Failed to fetch asset model data\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
            except requests.RequestException as request_error:
                logger.error(f"Request error during asset model creation: {request_error}")
                raise HTTPException
        except Exception as e:
            msg = f"Error while creating Asset model parameter: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_tags_groups(self, tag_group, each_asset_model):
        try:
            payload = copy.deepcopy(AssetModelConstants.tag_data)
            payload["type"] = "tag_groups"
            tag_group_id = {"tag_group_id": tag_group}
            payload.update(tag_group_id)
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.asset_tag_meta}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                asset_model_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking asset model existence: {request_error}")
                raise HTTPException
            if asset_model_data:
                list_tags = []
                for each_drop_down in asset_model_data:
                    tags = [each_asset_model.strip() for each_asset_model in
                            each_asset_model["parameter_groups/parameter_category"].replace('\n', '').split(',')]
                    if any(each_tag.lower() == each_drop_down["tag_group_name"].lower() for each_tag in tags):
                        list_tags.append(each_drop_down["tag_id"])
                return list_tags
            return {}
        except Exception as e:
            msg = f"Error while getting Asset model tags: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_tags_category(self, tag_category, each_asset_model):
        try:
            payload = copy.deepcopy(AssetModelConstants.tag_data)
            payload["type"] = "tag_category"
            tag_group_id = {"tag_category_id": tag_category}
            payload.update(tag_group_id)
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.asset_tag_meta}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)
                if response.status_code != 200:
                    msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                asset_model_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking asset model existence: {request_error}")
                raise HTTPException
            if asset_model_data:
                list_tags = []
                for each_drop_down in asset_model_data:
                    tags = [each_asset_model.strip() for each_asset_model in
                            each_asset_model["parameter_groups/parameter_category"].replace('\n', '').split(',')]
                    if any(each_tag.lower() == each_drop_down["tag_category_name"].lower() for each_tag in tags):
                        list_tags.append(each_drop_down["tag_id"])
                return list_tags
            return {}
        except Exception as e:
            msg = f"Error while getting Asset model tags: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_asset_tag_group(self, each_asset_model):
        try:
            payload = copy.deepcopy(AssetModelConstants.tag_data)
            payload["type"] = "tag_groups"
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.asset_tag}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)
                if response.status_code != 200:
                    msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                asset_model_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking asset model existence: {request_error}")
                raise HTTPException
            if asset_model_data:
                list_tags = []
                for each_drop_down in asset_model_data:
                    tags = [each_asset_model.strip() for each_asset_model in
                            each_asset_model["parameter_groups/parameter_category"].replace('\n', '').split(',')]
                    if any(each_tag.lower() == each_drop_down["tag_group_name"].lower() for each_tag in tags):
                        list_tags.append(each_drop_down["tag_group_id"])
                return True, list_tags
            return False, {}
        except Exception as e:
            msg = f"Error while fetching Asset model parameter group: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_asset_tag_category(self, each_asset_model):
        try:
            payload = copy.deepcopy(AssetModelConstants.tag_data)
            payload["type"] = "tag_category"
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.asset_tag}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)
                if response.status_code != 200:
                    msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                asset_model_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking asset model existence: {request_error}")
                raise HTTPException
            if asset_model_data:
                list_tags = []
                for each_drop_down in asset_model_data:
                    tags = [each_asset_model.strip() for each_asset_model in
                            each_asset_model["parameter_groups/parameter_category"].replace('\n', '').split(',')]
                    if any(each_tag.lower() == each_drop_down["tag_category_name"].lower() for each_tag in tags):
                        list_tags.append(each_drop_down["tag_category_id"])
                return True, list_tags
            return False, {}
        except Exception as e:
            msg = f"Error while fetching Asset model parameter category: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_drop_down_data(self, each_asset_model):
        try:
            payload = copy.deepcopy(AssetModelConstants.drop_down_data)
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.drop_down_list}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                asset_model_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking asset model existence: {request_error}")
                raise HTTPException
            if asset_model_data:
                for each_drop_down in asset_model_data:
                    if each_asset_model["industry"].lower() == each_drop_down["industry_category_name"].lower():
                        return True, each_drop_down
            return False, {}
        except Exception as e:
            msg = f"Error while fetching Asset model drop down data: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def check_asset_model_exits(self):
        try:
            payload = copy.deepcopy(AssetModelConstants.asset_model_content_json)
            filter_data_template = copy.deepcopy(AssetModelConstants.asset_model_filters)
            for each_data in self.asset_list:
                filter_data = filter_data_template.copy()
                filter_data['showFiltersSidebar'] = each_data.get('asset_model_name', '').strip()
                filter_data['search'] = True
                payload['filters']['filterModel'] = filter_data
                url = f'{EnvironmentConstants.base_path}{AssetModelAPI.asset_model_list}'
                try:
                    if self.encrypt_payload:
                        payload_encoded = JWT().encode(payload=payload)
                        response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                                 cookies=self.login_token)
                    else:
                        response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                    if response.status_code != 200:
                        msg = f"Failed to fetch asset model data. Status code: {response.status_code}, Response: {response.text}\n"
                        logger.error(msg)
                        self.response_messages += msg
                        raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                    response_json = response.json()
                    asset_model_data = response_json.get('data', {}).get('tableData', {}).get('bodyContent', [])
                    if asset_model_data:
                        return True, asset_model_data
                except requests.RequestException as request_error:
                    logger.error(f"Request error while checking asset model existence: {request_error}")
                    raise HTTPException
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching asset model data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def add_next_version(self, each_asset_model, existing_asset_model_data):
        try:
            payload_data = copy.deepcopy(AssetModelConstants.asset_model_creation_json)
            if each_asset_model["increment_version"].lower() == "yes":
                for each_data in existing_asset_model_data:
                    payload_data["asset_model_id"] = each_data["asset_model_id"]
                    payload_data['asset_version'] = each_data['asset_version']
                    if each_data['asset_model_name'] == each_asset_model['asset_model_name']:
                        asset_model_data = self.create_asset_model_basic_info(payload_data=payload_data,
                                                                              each_asset_model=each_asset_model)
                        if asset_model_data:
                            self.create_asset_model_parameters(payload_data=payload_data, each_asset_model=each_asset_model,
                                                               asset_model_data=asset_model_data)
                            msg = f"Incremented the version of the Asset Model: {each_asset_model['asset_model_name']}\n"
                            logger.info(msg)
                            self.response_messages += msg

        except Exception as e:
            msg = f"Error while creating Asset model: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)
