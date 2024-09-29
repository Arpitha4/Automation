import copy
import re

import pandas as pd
import openpyxl
import requests

from fastapi import HTTPException, status

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import ParametersAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.parameter_constants import ParameterConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class ParameterCreationHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None,
                 response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.parameter_metadata = dict()
        self.parameter_list = []

    def automate_parameter_creation(self):
        try:
            logger.info("Initiated parameter creation automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.parameter)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)
            df = self.extract_parameter_data(merged_row_groups, df)
            self.convert_parameter_metadata_to_dict(df)

            _, parameter_data = self.check_parameter()

            tag_types, data_types, unit_data, tag_groups, parameter_category = map(lambda f: f(),
                                                                                   [self.get_tag_types,
                                                                                    self.get_data_types,
                                                                                    self.get_unit_data,
                                                                                    self.get_tag_groups,
                                                                                    self.list_parameter_category])

            data_types_data = {parameter['data_type_name'] for parameter in self.parameter_list if
                               'data_type_name' in parameter}
            tag_types_data = {parameter['tag_type_name'] for parameter in self.parameter_list if
                              'tag_type_name' in parameter}
            unit_data_data = {parameter['unit_name'] for parameter in self.parameter_list if 'unit_name' in parameter}
            tag_groups_data = {parameter['tag_group_name'] for parameter in self.parameter_list if
                               'tag_group_name' in parameter}
            parameter_category_data = {parameter['parameter_category'] for parameter in self.parameter_list if
                                       'parameter_category' in parameter}
            data_source_data = {parameter['system_tag_label'] for parameter in self.parameter_list if
                                'system_tag_label' in parameter}

            filter_data_source = self.filter_platform_data(tag_types[2], data_source_data) if tag_types[0] else []
            filtered_tag_types = self.filter_platform_data(tag_types[1], tag_types_data) if tag_types[0] else []
            filtered_data_types = self.filter_platform_data(data_types[1], data_types_data) if data_types[0] else []
            filtered_unit_data = self.filter_platform_data(unit_data[1], unit_data_data) if unit_data[0] else []
            filtered_tag_groups = self.filter_platform_data(tag_groups[1], tag_groups_data) if tag_groups[0] else []
            filtered_parameter_category = self.filter_platform_data(parameter_category[1], parameter_category_data) if \
                parameter_category[0] else []

            labels = [item['label'] for item in
                      filter_data_source + filtered_tag_types + filtered_data_types + filtered_unit_data + filtered_tag_groups + filtered_parameter_category]

            existing_tag_name = [category["tag_name"].lower() for category in parameter_data]
            new_tag_name = [category["tag_name"].lower() for category in self.parameter_list]

            added_categories = []
            removed_categories = []

            for new_tag in new_tag_name:
                if new_tag not in existing_tag_name:
                    added_categories.append(new_tag)

            for existing_tag in existing_tag_name:
                if existing_tag not in new_tag_name:
                    removed_categories.append(existing_tag)

            if added_categories or removed_categories:
                logger.info("Initiated update for Parameter Information!!")
                for parameter in self.parameter_list:
                    parameter_values = self.validate_and_collect_values(parameter)

                    logger.debug(f"Checking parameter values: {parameter_values}")

                    required_fields = ['data_type_name', 'tag_group_name', 'parameter_category']
                    missing_fields = [field for field in required_fields if
                                      not parameter_values.get(field) or parameter_values.get(field) not in labels]

                    if missing_fields:
                        msg = f"Skipping parameter creation for {parameter['tag_name']} due to missing values: {missing_fields}\n"
                        logger.info(msg)
                        self.response_messages += msg
                        continue

                    logger.info(f"Creating parameter with values: {parameter_values}")
                    create_param_data = {
                        'system_tag_label': filter_data_source,
                        'tag_types': filtered_tag_types,
                        'data_types': filtered_data_types,
                        'unit_data': filtered_unit_data,
                        'tag_groups': filtered_tag_groups,
                        'parameter_category': filtered_parameter_category,
                    }

                    self.create_parameter(**create_param_data)
                    msg = "Completed Parameter Creation\n"
                    self.response_messages += msg
            else:
                msg = f"Parameter {existing_tag_name} Information Exists\n"
                logger.info(msg)
                self.response_messages += msg

            return self.response_messages
        except Exception as parameter_error:
            msg = f"Unexpected error while automating parameter: {parameter_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def filter_platform_data(self, data, valid_labels):
        return [item for item in data if item['label'] in valid_labels]

    def validate_and_collect_values(self, parameter):
        required_fields = ['tag_name', 'description', 'system_tag_label']
        missing_required_fields = [field for field in required_fields if not parameter.get(field)]

        if parameter.get('system_tag_label') in ['Design', 'HMI', 'Manual', 'Meta', 'Product']:
            if not parameter.get('data_type_name') or not parameter.get('tag_type_name'):
                missing_required_fields.extend(['data_type_name', 'tag_type_name'])

        if missing_required_fields:
            logger.warning(f"Parameter missing required fields: {parameter}")
            raise ValueError(f"Missing required fields in the parameter: {', '.join(missing_required_fields)}")

        parameter_values = {
            'unit_name': parameter.get('unit_name'),
            'tag_group_name': parameter.get('tag_group_name'),
            'system_tag_label': parameter.get('system_tag_label'),
            'parameter_category': parameter.get('parameter_category'),
            'data_type_name': parameter.get('data_type_name'),
            'tag_type_name': parameter.get('tag_type_name'),
        }

        return parameter_values

    def extract_parameter_data(self, merged_row_groups, df):
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
            msg = f"Error while extracting parameter data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_parameter_metadata_to_dict(self, df):
        try:
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[1]
            if self.response_messages is None:
                self.response_messages = ""
            self.parameter_list = []
            for row in range(2, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = ParameterConstants.meta_data_mapping.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'tag_name':
                        if pd.isna(metadata_value[col]):
                            self.response_messages += 'Parameter is missing\n'
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.parameter_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting parameter metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_parameter(self, tag_types, data_types, unit_data, tag_groups, parameter_category, system_tag_label):
        try:
            url = f'{EnvironmentConstants.base_path}{ParametersAPI.save_parameter}'

            # Create mappings from label to value for easy lookup
            tag_type_mapping = {item['label']: item['value'] for item in tag_types}
            data_type_mapping = {item['label']: item['value'] for item in data_types}
            unit_data_mapping = {item['label']: item['value'] for item in unit_data}
            tag_group_mapping = {item['label']: item['value'] for item in tag_groups}
            parameter_category_mapping = {item['label']: item['value'] for item in parameter_category}
            system_tag_label_mapping = {item['label']: item['value'] for item in system_tag_label}

            for each_data in self.parameter_list:
                payload_data = copy.deepcopy(ParameterConstants.parameter_json)
                numeric_limit, string_length = self.data_quality_info(each_data=each_data)
                data_quality_basic = self.data_quality_basic(each_data=each_data)

                payload_data["tag_name"] = each_data.get('tag_name', '')
                payload_data["description"] = each_data.get('description', '')
                payload_data["unit_name"] = each_data.get('unit', '')
                payload_data["tag_group_name"] = each_data.get('tag_group_name', '')
                payload_data["system_tag_label"] = each_data.get('system_tag_label', '')
                payload_data["parameter_category"] = each_data.get('parameter_category', '')
                payload_data["tag_type_name"] = each_data.get('tag_type_name', '')
                payload_data["tag_label"] = each_data.get('tag_label', '')
                payload_data["data_type_name"] = each_data.get('data_type_name', '')
                payload_data["data_quality_info"]["numeric_limit"] = numeric_limit
                payload_data["data_quality_info"]["string_length"] = string_length
                payload_data["data_quality_info"]["basic"] = data_quality_basic

                # Look up values based on the label in self.parameter_list
                if payload_data["tag_type_name"] in tag_type_mapping:
                    payload_data["tag_type"] = tag_type_mapping[payload_data["tag_type_name"]]
                if payload_data["data_type_name"] in data_type_mapping:
                    payload_data["data_type"] = data_type_mapping[payload_data["data_type_name"]]
                if payload_data["unit_name"] in unit_data_mapping:
                    payload_data["unit"] = unit_data_mapping[payload_data["unit_name"]]
                if payload_data["tag_group_name"] in tag_group_mapping:
                    payload_data["tag_group_id"] = tag_group_mapping[payload_data["tag_group_name"]]
                if payload_data["parameter_category"] in parameter_category_mapping:
                    payload_data["tag_category_id"] = parameter_category_mapping[payload_data["parameter_category"]]
                if payload_data["system_tag_label"] in system_tag_label_mapping:
                    payload_data["system_tag_type"] = system_tag_label_mapping[payload_data["system_tag_label"]]

                # Send the request for the current parameter
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload_data)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload_data, headers=Secrets.headers, cookies=self.login_token)

                # Check the response status
                if response.status_code != 200:
                    msg = f"Failed to fetch parameter data for {payload_data['tag_name']}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)

        except Exception as metadata_error:
            msg = f"Error while updating the parameter data: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def data_quality_info(self, each_data):
        try:
            numeric_limit = {}
            string_length = {}
            numeric_limit_str = str(each_data.get('numeric_limit', ''))
            string_length_str = str(each_data.get('string_length', ''))
            if numeric_limit_str:
                numeric_limit_match = re.match(r"(\d+)-(\d+)", numeric_limit_str)
                if numeric_limit_match:
                    numeric_min_limit = int(numeric_limit_match.group(1))
                    numeric_max_limit = int(numeric_limit_match.group(2))
                    numeric_limit = {
                        "min": int(numeric_min_limit),
                        "max": int(numeric_max_limit)
                    }
            if string_length_str:
                string_length_match = re.match(r"(\d+)-(\d+)", string_length_str)
                if string_length_match:
                    string_length_min_limit = int(string_length_match.group(1))
                    string_length_max_limit = int(string_length_match.group(2))
                    string_length = {
                        "min": int(string_length_min_limit),
                        "max": int(string_length_max_limit)
                    }
            return numeric_limit, string_length
        except Exception as data_error:
            msg = f"Error while creating data quality data: {data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def data_quality_basic(self, each_data):
        try:
            value = bool(each_data.get('basic', ''))
            required = bool(each_data.get('required', ''))
            basic_info = {
                "value": value,
                "required": required
            }
            return basic_info
        except Exception as data_error:
            msg = f"Error while creating data quality data: {data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def check_parameter(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_content_json)
            filter_data_template = copy.deepcopy(ParameterConstants.parameter_filter_model)
            results = []

            for each_data in self.parameter_list:
                filter_data = filter_data_template.copy()
                filter_data['tag_name']['filter'] = each_data.get('tag_name', '').strip()
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

    def get_tag_types(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_payload)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_tag_types}'
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
            tag_type = response_json.get('data', {})
            system_tag_type = response_json.get('system_tag_type', {})
            if tag_type and system_tag_type:
                return True, tag_type, system_tag_type
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def get_data_types(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_payload)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_data_types}'
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
            data_type = response_json.get('data', {})
            if data_type:
                return True, data_type
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def get_unit_data(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_payload)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_unit_data}'
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
            data_type = response_json.get('data', {})
            if data_type:
                return True, data_type
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def get_tag_groups(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_payload)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_tag_groups}'
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
            data_type = response_json.get('data', {})
            if data_type:
                return True, data_type
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def list_parameter_category(self):
        try:
            payload = copy.deepcopy(ParameterConstants.list_parameter_category)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.list_parameter_category}'
            if self.encrypt_payload:
                payload_encoded = JWT().encode(payload)
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
            parameter_category = response_json.get('data', {})
            if parameter_category:
                return True, parameter_category
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)
