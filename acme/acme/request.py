import requests

from typing import Dict, Optional

from .decorator import http_exception


class Request:
    def __init__(self, validation: str) -> None:
        self._requester_base = requests
        self.validation = validation

    @http_exception
    def get(self, url: str, headers: Dict = {}, query_params: Dict = {}):
        if self.validation == 'False':
            return self._requester_base.get(url, headers=headers, params=query_params, verify=False)
        else:
            return self._requester_base.get(url, headers=headers, params=query_params)

    @http_exception
    def post(self, url: str, files: Optional[Dict] = {}, headers: Dict = {}, data: Dict = {}):
        if self.validation == 'False':
            return self._requester_base.post(url, files=files, headers=headers, data=data, verify=False)
        else:
            return self._requester_base.post(url, files=files, headers=headers, data=data)

    @http_exception
    def put(self, url: str, headers: Dict = {}, data: Dict = {}):
        if self.validation == 'False':
            return self._requester_base.put(url, headers=headers, data=data, verify=False)
        else:
            return self._requester_base.put(url, headers=headers, data=data)

    @http_exception
    def delete(self, url: str, headers: Dict = {}):
        if self.validation == 'False':
            return self._requester_base.delete(url, headers=headers, verify=False)
        else:
            return self._requester_base.delete(url, headers=headers)
