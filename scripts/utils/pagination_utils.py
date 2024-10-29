import requests
from fastapi import HTTPException

from scripts.constants.app_constants import Secrets
from scripts.logging.logger import logger
from scripts.utils.security_utils.jwt_util import JWT


class PaginationUtils:

    def pagination_function(self, url, payload, encrypt_payload, login_token):
        try:
            results = []
            page = 1
            end_records = False

            while not end_records:
                payload['page'] = page
                payload['startRow'] = (page - 1) * payload['records']
                payload['endRow'] = page * payload['records']

                # Encode payload in JWT if needed
                if encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    raise HTTPException(status_code=response.status_code, detail=msg)

                response_json = response.json()
                body_content = response_json.get('data', {}).get('bodyContent', [])
                if body_content:
                    results.extend(body_content)
                else:
                    end_records = True
                page += 1
            return results
        except Exception as pagination_error:
            logger.error(pagination_error)
