import copy
import pandas as pd
import openpyxl
import requests

from fastapi import HTTPException

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import AssetModelAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.industry_constants import IndustryConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class IndustryHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None,
                 response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages or ""
        self.industry_metadata = dict()
        self.industry_list = []

    def automate_industry(self):
        try:
            logger.info("Initiated industry automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.industry)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_industry_data(merged_row_groups, df)
            self.convert_industry_metadata_to_dict(df)
            _, drop_down_data = self.get_drop_down_data()
            existing_industry = [industry["industry_category_name"].lower() for industry in drop_down_data]
            new_industry = [industry["industry"].lower() for industry in self.industry_list]

            added_model = []
            existing_model = []
            for new_tag in new_industry:
                if new_tag not in existing_industry:
                    added_model.append(new_tag)
            for existing_tag in existing_industry:
                if existing_tag not in new_industry:
                    existing_model.append(existing_tag)
            if added_model:
                logger.info("Initiated Industry Creation!!")
                for each_industry in self.industry_list:
                    if each_industry["industry"].lower() in added_model:
                        self.create_industry(each_industry=each_industry)
                msg = f"Created Industry : {new_industry} "
                logger.info(msg)
                self.response_messages += msg
                if added_model:
                    logger.info(f"Added Industry: {', '.join(added_model)}")
                if existing_model:
                    logger.info(f"Existing Industry: {', '.join(existing_model)}")
            else:
                msg = f"Industry Information Exists: {existing_industry} "
                logger.info(msg)
                self.response_messages += msg
            return self.response_messages
        except Exception as industry_error:
            msg = f"Error while automating industry: {industry_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def extract_industry_data(self, merged_row_groups, df):
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
            msg = f"Error while extracting industry data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_industry_metadata_to_dict(self, df):
        try:
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[0]
            for row in range(1, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = IndustryConstants.industry_meta_data.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'industry':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Industry is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'description':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Description is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.industry_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting Industry metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_industry(self, each_industry):
        try:
            payload = copy.deepcopy(IndustryConstants.create_drop_down)
            payload["industry_category_name"] = each_industry.get('industry', '')
            payload["description"] = each_industry.get('description', '')

            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.create_drop_down}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)
                if response.status_code != 200:
                    msg = f"Failed to fetch industry data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking industry existence: {request_error}")
                raise HTTPException
        except Exception as e:
            msg = f"Error while creating industry drop down data: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def get_drop_down_data(self):
        try:
            payload = copy.deepcopy(IndustryConstants.drop_down_data)
            url = f'{EnvironmentConstants.base_path}{AssetModelAPI.drop_down_list}'
            try:
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)
                if response.status_code != 200:
                    msg = f"Failed to fetch industry data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
                response_json = response.json()
                industry_data = response_json.get('data', [])
            except requests.RequestException as request_error:
                logger.error(f"Request error while checking industry existence: {request_error}")
                raise HTTPException
            if industry_data:
                return True, industry_data
            return False, {}
        except Exception as e:
            msg = f"Error while fetching industry drop down data: {e}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)
