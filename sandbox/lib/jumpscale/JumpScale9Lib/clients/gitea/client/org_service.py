# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.
from .Repository import Repository
from .unhandled_api_error import UnhandledAPIError
from .unmarshall_error import UnmarshallError


class OrgService():
    def __init__(self, client):
        pass
        self.client = client

    def createOrgRepo(self, data, org, headers=None, query_params=None, content_type="application/json"):
        """
        Create a repository in an organization
        It is method for POST /org/{org}/repos
        """
        uri = self.client.base_url + "/org/" + org + "/repos"
        resp = self.client.post(uri, data, headers, query_params, content_type)
        try:
            if resp.status_code == 201:
                return Repository(resp.json()), resp

            message = 'unknown status code={}'.format(resp.status_code)
            raise UnhandledAPIError(response=resp, code=resp.status_code,
                                    message=message)
        except ValueError as msg:
            raise UnmarshallError(resp, msg)
        except UnhandledAPIError as uae:
            raise uae
        except Exception as e:
            raise UnmarshallError(resp, e.message)
