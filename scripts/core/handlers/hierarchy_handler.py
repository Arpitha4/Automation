import copy

import pandas as pd
import openpyxl
import requests
from fastapi import HTTPException
from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import HierarchyAPI, ParametersAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.hierarchy_constants import HierarchyConstants
from scripts.constants.parameter_constants import ParameterConstants

from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class HierarchyHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None, response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.hierarchy_metadata = dict()
        self.hierarchy_list = []
        self.hierarchy_input_list = []

    def hierarchy_automation(self):
        try:
            logger.info("Initiated Hierarchy Automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.hierarchy)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_unit_data(merged_row_groups, df)
            self.convert_unit_metadata_to_dict(df)
            hierarchy_data = self.fetch_hierarchy_data()
            for item in self.hierarchy_list:
                if 'tags' in item and isinstance(item['tags'], str):
                    cleaned_tags = [tag.strip() for tag in item['tags'].replace('\n', '').split(',')]
                    _, parameter_data = self.check_parameter(cleaned_tags)
                    self.hierarchy_input_list = []
                    hierarchy_name = item["name"]
                    hierarchy_parts = hierarchy_name.split('>')
                    child_data = None
                    for index in range(len(hierarchy_parts)):
                        full_hierarchy = ">".join(hierarchy_parts[:index + 1])
                        for each_hry in hierarchy_data[1]:
                            if full_hierarchy == each_hry["full_name"]:
                                # if index == len(hierarchy_parts) - 1:
                                child_data = each_hry
                                # else:
                                #     parent_data = each_data
                    if child_data:
                        self.update_hierarchy(child_data=child_data, parameter_data=parameter_data)
                        parameter_data = None

                        msg = "Updated Hierarchy Category Information "
                        logger.info(msg)
                        self.response_messages += msg

            return self.response_messages
        except Exception as e:
            msg = f"Error while automating hierarchy: {e}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def extract_unit_data(self, merged_row_groups, df):
        try:
            group_dfs = []
            for each in merged_row_groups:
                group_df = df.iloc[each].reset_index(drop=True)
                group_df.dropna(how='all', inplace=True)
                group_df.dropna(how='all', axis=1, inplace=True)
                group_dfs.append(group_df)
            result_df = pd.concat(group_dfs, ignore_index=True)
            return result_df
        except Exception as extraction_error:
            msg = f"Error while extracting hierarchy data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_unit_metadata_to_dict(self, df):
        try:
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[0]
            if self.response_messages is None:
                self.response_messages = ""
            for row in range(1, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = HierarchyConstants.hierarchy_meta_data.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'name':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Hierarchy is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'tags':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Hierarchy is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.hierarchy_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting unit metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def fetch_hierarchy_data(self):
        try:
            payload = copy.deepcopy(HierarchyConstants.payload_data)

            url = f'{EnvironmentConstants.base_path}{HierarchyAPI.fetch_hierarchy}'

            if self.encrypt_payload:
                payload_encoded = JWT().encode(payload=payload)
                response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                         cookies=self.login_token)
            else:
                response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

            if response.status_code != 200:
                msg = f"Failed to fetch hierarchy data. Status code: {response.status_code}, Response: {response.text}\n"
                logger.error(msg)
                self.response_messages += msg
                raise HTTPException(status_code=response.status_code, detail=self.response_messages)
            response_json = response.json()
            unit_group_data = response_json.get('data', {})
            if unit_group_data:
                return True, unit_group_data
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching hierarchy data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def check_parameter(self,cleaned_tags):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_content_json)
            filter_data_template = copy.deepcopy(ParameterConstants.parameter_filter_model)
            results = []


            for tags in cleaned_tags:
                filter_data = filter_data_template.copy()
                filter_data['tag_name']['filter'] = tags
                payload['filters']['filterModel'] = filter_data

                url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_parameter_content}'
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch parameter data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)

                response_json = response.json()
                parameter_category_data = response_json.get('data', {}).get('bodyContent', [])
                if parameter_category_data:
                    results.append(parameter_category_data[0])

            return True, results
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def update_tags(self, each_data, parameter_data):
        tags_data = []
        existing_tags = {tag["value"] for tag in each_data.get("tags", [])}

        logger.debug(f"Initial existing_tags for {each_data['node_id']}: {existing_tags}")
        logger.debug(f"Parameter data: {parameter_data}")

        for each_param in parameter_data:
            tag_value = each_param["tag_id"]
            tag_label = each_param["tag_name"]
            if tag_value not in existing_tags:
                tags_data.append({"value": tag_value, "label": tag_label})
                existing_tags.add(tag_value)
                logger.debug(f"Added tag: {{'value': {tag_value}, 'label': {tag_label}}}")

        logger.debug(f"New tags to be added for {each_data['node_id']}: {tags_data}")
        return tags_data

    def update_hierarchy(self, child_data, parameter_data):
        try:
            payload_data = copy.deepcopy(HierarchyConstants.hierarchy_save_payload)
            payload_data["type"] = child_data["type"]
            payload_data["node_id"] = child_data["node_id"]
            payload_data["node_name"] = child_data["name"]
            payload_data["parent_id"] = child_data["parent_id"]
            for each_item in payload_data["data"]:
                each_item.update({
                    "node_id": child_data["node_id"],
                    "name": child_data["name"],
                    "parent_id": child_data["parent_id"],
                    "type": child_data["type"],
                    "description": child_data["desc"],
                })
                each_item.update(child_data["info"])
                each_item.update(child_data["settings"])

                logger.debug(f"Initial each_data before tags update: {each_item}")
                new_tags = self.update_tags(each_item, parameter_data)

                each_item["tags"].extend(new_tags)

                logger.debug(f"Updated each_data after tags: {each_item}")

            # Construct the API URL
            url = f'{EnvironmentConstants.base_path}{HierarchyAPI.save_hierarchy}'

            if self.encrypt_payload:
                payload = JWT().encode(payload=payload_data)
                response = requests.post(url, data=payload, headers=Secrets.headers, cookies=self.login_token)
            else:
                response = requests.post(url, json=payload_data, headers=Secrets.headers, cookies=self.login_token)

            if response.status_code != 200:
                msg = "Failed to fetch hierarchy data\n"
                logger.error(msg)
                self.response_messages += msg
                raise HTTPException(status_code=response.status_code, detail=self.response_messages)

        except Exception as metadata_error:
            msg = f"Error while updating the hierarchy data: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)


