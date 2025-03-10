from typing import Any, Dict, Iterator, List, Optional, TYPE_CHECKING
from httpx import Client, HTTPError

from .exceptions import raise_error
from .models import AccountRole


if TYPE_CHECKING:
    from typing import Literal
    from .models import Package


class GravityZone:
    items_per_page: int = 30  # max: 100

    def __init__(
        self,
        access_url: str,
        api_key:    str,
    ):
        self.client = Client(
            base_url='/'.join((access_url.rstrip('/'), 'v1.0/jsonrpc/')),
            auth=(api_key, ''),
        )

    def call(
        self,
        endpoint: str,
        method:   str,
        params:   Dict[str, Any],
        service:  Optional[str] = None,
        timeout: int = 30
    ):
        body = {'id': 1, 'jsonrpc': '2.0', 'method': method, 'params': params}
        path = '/'.join(filter(None, (endpoint, service)))
        resp = self.client.post(path, json=body, timeout=timeout)
        try:
            resp.raise_for_status()
        except HTTPError as e:
            raise_error(e.request, e.response)

            # # TODO: check if API is enabled
            # enabled_apis = self.get_api_key_details()['enabledApis']
            # if endpoint.lower() not in enabled_apis:
            #     raise Exception(f'API {endpoint!r} not enabled for this key')

        try:
            return resp.json()['result']
        except KeyError:
            raise_error(resp.request, resp)

    def paginate(
        self,
        endpoint: str,
        method:   str,
        params:   Dict[str, Any],
        service:  Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        page = 1

        while True:
            params.update({'page': page, 'perPage': self.items_per_page})
            resp = self.call(endpoint, method, params, service)
            
            if resp.get('total') == 0:
                break
            
            yield from resp['items']

            if resp['page'] == resp['pagesCount']:
                break
            page += 1

# region ACCOUNTS
    def get_accounts(self, company_id: Optional[str] = None):
        '''Returns the user accounts visible to the account which has
        generated the API key.
        '''
        params = {'companyId': company_id}
        return self.paginate('accounts', 'getAccountsList', params)

    def get_account_detail(self, account_id: str):
        '''Returns the user accounts visible to the account which has
        generated the API key.
        '''
        params = {'accountId': account_id}
        return self.call('accounts', 'getAccountDetails', params)

    def create_account(
            self,
            email:      str,
            password:   str,
            target_ids: List[str],
            company_id: str = '675fd66b42b81864630be143',
            role:       AccountRole = 5
        ) -> str:
        '''Creates a user account with the specified email, password, and role, then returns the account ID.

        Args:
            email (str): The email address for the new account.
            password (str): The password for the new account.
            company_id (Optional[str], optional): The ID of the company to associate the account with. 
                Defaults to '675fd66b42b81864630be143' Mobifone company.
            role (AccountRole, optional): The role assigned to the user. Defaults to 5. 
                Possible values:
                    1 - Company Administrator
                    2 - Network Administrator
                    3 - Reporter
                    4 - Partner
                    5 - Custom
            target_ids (List[str], optional): A list of target IDs associated with the account. Defaults to None.

        Returns:
            str: The newly created account's ID.
        '''
        params = {
           "email": email,
           "profile": {
                "fullName": f'Khách hàng Mobifone',
               "language": "vi_VN",
               "timezone": "Asia/Ho_Chi_Minh"
           },
           "password": password,
           "role": role,
           "rights": {
               "manageCompanies": False,
               "companyManager": False,              
               "manageInventory": True,
               "managePoliciesRead": True,
               "managePoliciesWrite": False,
               "manageRemoteShell": True,
               "manageReports": True,
               "manageUsers": False
           },
           "companyId": company_id,
           "targetIds": target_ids
        }
        return self.call('accounts', 'createAccount', params)

    def update_account_password(self, account_id: str, password: str) -> None:
        '''Updates the password for a given user account.

        Args:
            account_id (str): The unique ID of the account to be updated.
            password (str): The new password to set for the account.

        Returns:
            None
        '''
        params = {
        "accountId": account_id,
        "password": password
        }
        return self.call('accounts', 'updateAccount', params)

    def update_target_ids_account(self, account_id: str, target_ids: List[str]) -> None:
        '''Updates the list of target IDs associated with a user account.

        Args:
            account_id (str): The unique ID of the account to be updated.
            target_ids (List[str]): A list of target IDs to associate with the account.

        Returns:
            None
        '''
        params = {
        "accountId": account_id,
        "targetIds": target_ids
        }
        return self.call('accounts', 'updateAccount', params)

    def delete_account(self, account_id: str) -> None:
        '''Deletes a user account by its unique ID.

        Args:
            account_id (str): The unique ID of the account to be deleted.

        Returns:
            None
        '''
        params = {'accountId': account_id}
        return self.call('accounts', 'deleteAccount', params)

    def get_notifications_settings(self, account_id: str) -> Dict[str, Any]:
        params = {'accountId': account_id}
        return self.call('accounts', 'getNotificationsSettings', params)

    def set_notifications_settings(self, **kwargs):
        raise NotImplementedError
# endregion

# region COMPANIES
    def get_company(self, company_id: Optional[str] = None):
        '''Returns the details of a company.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
        '''
        params = {'companyId': company_id}
        return self.call('companies', 'getCompanyDetails', params)

    def get_company_by_user(self, username: str, password: str):
        '''Retrieves the details of a company linked to an account
        identified through the given username.
        '''
        params = {'username': username, 'password': password}
        return self.call('companies', 'getCompanyDetailsByUser', params)

    def find_companies_by_name(self, filter):
        params = {'nameFilter': filter}
        return self.call('companies', 'findCompaniesByName', params)

    def create_company(
        self,
        name: str,
        reservedSlots:     int,
        licenseKey:        Optional[str] = None,
        companyType:       int = 1, 
        licenseType:       int = 3,
        assignedProductType: int = 0,
        manageRemoteEnginesScanning: bool = False,
        manageHyperDetect: bool = False,
        manageSandboxAnalyzer: bool = False,
        endSubscription:    Optional[str] = None,
        address:            Optional[str] = None,
        phone:              Optional[str] = None,
        managed_by_partner: bool = True
    ):
        """
        Creates a company with the specified attributes.

        Args:
            companyType (int): The type of the company (default: 1 for Customer).
            name (str): The unique name of the company.
            licenseType (int): The type of license (default: 3 for Monthly subscription), 2 (license)

            assignedProductType (int): The product type assigned (default: 0 for Endpoint Security).
            endSubscription (str): Subscription end date in YYYY-MM-DD format.
            manageRemoteEnginesScanning (bool): Enables remote engine scanning (default: True).
            manageHyperDetect (bool): Enables HyperDetect add-on (default: False).
            manageSandboxAnalyzer (bool): Enables Sandbox Analyzer add-on (default: False).
            address (Optional[str]): The company's address (default: None).
            phone (Optional[str]): The company's phone number (default: None).
            managed_by_partner (bool): Indicates if managed by a partner (default: True).

        Returns:
            company_id (str)
        """
        if licenseType == 2:
            params = {
                'type':                companyType,
                'name':                name,
                'address':             address,
                'phone':               phone,
                'canBeManagedByAbove': managed_by_partner,
                "licenseSubscription": {
                            "type": licenseType, 
                            "licenseKey": licenseKey
                        },
            }
        else:
            params = {
                'type':                companyType,
                'name':                name,
                'address':             address,
                'phone':               phone,
                'canBeManagedByAbove': managed_by_partner,
                "licenseSubscription": {
                            "type": licenseType,
                            "reservedSlots": reservedSlots,
                            "assignedProductType": assignedProductType,
                            "ownUse": {
                                "manageRemoteEnginesScanning": manageRemoteEnginesScanning,
                                "manageHyperDetect": manageHyperDetect,
                                "manageSandboxAnalyzer": manageSandboxAnalyzer,
                            },
                        },
            }   
        return self.call('companies', 'createCompany', params)

    def update_company(
        self,
        company_id: str,
        name: str,
        companyType:       int = 1, 
        address:            Optional[str] = None,
        phone:              Optional[str] = None,
    ):
        """
        Update a company with the specified attributes.

        Args:
            companyType (int): The type of the company (default: 1 for Customer).
            name (str): The unique name of the company.
            address (Optional[str]): The company's address (default: None).
            phone (Optional[str]): The company's phone number (default: None).
        Returns:
            None
        """
        params = {
            'id':                  company_id,       
            'type':                companyType,
            'name':                name,
            'address':             address,
            'phone':               phone,
        }
        return self.call('companies', 'updateCompanyDetails', params)

    def delete_company(self, company_id: str) -> None:
        '''Delete an company account.

        Args:
            company_id: The ID of the company to be delete.
        '''
        params = {'companyId': company_id}
        return self.call('companies', 'deleteCompany', params)

    def suspend_company(self, company_id: str, recursive: bool) -> None:
        '''Suspends an active company account.

        Args:
            company_id: The ID of the company to be suspended.
            recursive: ``True`` if sub-companies should be suspended as
                well.
        '''
        params = {'companyId': company_id, 'recursive': recursive}
        return self.call('companies', 'suspendCompany', params)

    def activate_company(self, company_id: str, recursive: bool) -> None:
        '''Activates a suspended company account.

        Args:
            company_id: The ID of the company to be activated.
            recursive: ``True`` if sub-companies should be activated as
                well.
        '''
        params = {'companyId': company_id, 'recursive': recursive}
        return self.call('companies', 'activateCompany', params)
# endregion

# region LICENSING
    def get_licenses(
        self,
        company_id: Optional[str] = None,
        return_all: bool = False,
    ):
        '''Returns the license information for a company.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
        '''
        params = {'companyId': company_id, 'returnAllProducts': return_all}
        # TODO: doesn't return an array (is this the behaviour for arrays with one item?)
        return self.call('licensing', 'getLicenseInfo', params)

    def update_license(
        self,
        company_id: Optional[str] = None,
        manageHyperDetect: bool = None,
        manageSandboxAnalyzer: bool = None,
    ):
        """
        Updates the license subscription for a company.

        Args:
            company_id (Optional[str]): The ID of the target company. If not provided,
                                        the company linked to the API key will be used.
            manageHyperDetect (bool): Whether to enable or disable HyperDetect management. Default is False.
            manageSandboxAnalyzer (bool): Whether to enable or disable Sandbox Analyzer management. Default is False.

        Returns:
            dict: The API response containing the updated license information.

        Raises:
            ValueError: If `company_id` is invalid.
            RuntimeError: If the API call fails.
        """
        # Validate company_id if provided
        if company_id is not None and not company_id.strip():
            raise ValueError("company_id must not be an empty string.")

        # Prepare API parameters
        params = {
            "companyId": company_id,
            "ownUse": {
                "manageHyperDetect": manageHyperDetect,
                "manageSandboxAnalyzer": manageSandboxAnalyzer,
            },
        }
        return self.call("licensing", "setMonthlySubscription", params)

    def set_license(self, company_id: str, licenseKey: str):
        """
        Sets a license key for a specified company by making an API call.

        This function validates the provided `company_id` to ensure it is not empty,
        then constructs the necessary parameters and sends a request to the API
        to set the license key for the company.

        Parameters:
            company_id (str): The unique identifier of the company.
                            Must not be an empty string.
            licenseKey (str): The license key to be assigned to the company.

        Raises:
            ValueError: If `company_id` is an empty string after stripping whitespace.

        Returns:
            Any: The response from the API call to the licensing system.

        Example:
            >>> client.set_license("12345", "ABC-XYZ-9876")
        """
        
        # Validate company_id if provided
        if company_id is not None and not company_id.strip():
            raise ValueError("company_id must not be an empty string.")

        # Prepare API parameters
        params = {
            "licenseKey": licenseKey,
            "companyId": company_id
        }

        # Call the API and return its response
        return self.call("licensing", "setLicenseKey", params)

# endregion

# region NETWORK
    def get_root_containers(self, company_id: Optional[str] = None):
        '''Returns the root containers for a company. A root container
        refers to special groups, such as: Companies, Network, Computers
        and Groups.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
        '''
        params = {'companyId': company_id}
        return self.call('network', 'getRootContainers', params)

    def get_network_inventory(self):
        raise NotImplementedError

    def get_companies(
        self,
        parent_id: Optional[str] = None,
        filters:   Optional[Dict[str, int]] = None,
    ):
        '''Returns the list of companies under a parent company or from
        a company folder.

        Args:
            parent_id: The parent company's ID or the company folder's
                ID. The default value is the ID of the parent company.
            filters: The filters to apply on the returned list. The
                filtering criteria are:
                - companyType:
                  - 0: partner companies
                  - 1: customer companies
                - licenseType:
                  - 1: companies with trial license key
                  - 2: companies with yearly license key
                  - 3: companies with monthly license key
        '''
        params = {'parentId': parent_id, 'filters': filters}
        return self.call('network', 'getCompaniesList', params)

    def get_custom_groups(self, **kwargs):
        raise NotImplementedError

    def get_endpoints(self, company_id: str):
        """
        Retrieves the list of endpoints for a specified company.

        Args:
            company_id (str): The ID of the company whose endpoints are to be fetched.

        Returns:
            Response from the 'getEndpointsList' API call.
        """
        params = {"parentId": company_id}
        return self.paginate('network', 'getEndpointsList', params)

    def get_endpoint(self, endpoint_id: str, include_log: bool = True):
        """
        Retrieves detailed information about a specific endpoint.

        Args:
            endpoint_id (str): The ID of the endpoint to be fetched.
            include_log (bool, optional): Whether to include scan logs in the response. Defaults to True.

        Returns:
            Response from the 'getManagedEndpointDetails' API call.
        """
        params = {
            "endpointId": endpoint_id,
            "options": {
                "includeScanLogs": include_log
            }
        }
        return self.call('network', 'getManagedEndpointDetails', params)

    def delete_endpoint(self, endpoint_id: str):
        """
        Deletes a specific endpoint.

        Args:
            endpoint_id (str): The ID of the endpoint to be deleted.

        Returns:
            Response from the 'deleteEndpoint' API call.
        """
        params = {
            "endpointId": endpoint_id
        }
        return self.call('network', 'deleteEndpoint', params)

    def create_scan_endpoint(self, endpoint_id: str, scan_type: int = 1) -> dict:
        """
        Initiates a scan task on the specified endpoint.

        Parameters:
            endpoint_id (str): The unique identifier of the endpoint to be scanned.
            scan_type (int): The type of scan to perform.
                            Available options:
                            1 - Quick Scan
                            2 - Full Scan
                            3 - Memory Scan
                            4 - Custom Scan (default: 1)

        Returns:
            dict: The response from the API.

        Raises:
            ValueError: If `scan_type` is invalid or `endpoint_id` is empty.
        """
        # Validate scan_type
        if scan_type not in {1, 2, 3, 4}:
            raise ValueError(f"Invalid scan_type {scan_type}. Must be one of: 1, 2, 3, 4.")
        
        # Validate endpoint_id
        if not endpoint_id.strip():
            raise ValueError("endpoint_id cannot be empty.")

        params = {
            "targetIds": [endpoint_id],
            "type": scan_type,
            "returnAllTaskIds": True,
        }
        return self.call("network", "createScanTask", params)

    def get_scan_tasks(sel, **kwargs):
        raise NotImplementedError
# endregion

# region PACKAGES
    def get_installation_links(
        self,
        company_id:   Optional[str] = None,
        package_name: Optional[str] = None
    ):
        '''Returns the installation links and full kits for a package.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
            package_name: If not set, all packages will be returned.
        '''
        params = {'companyId': company_id, 'packageName': package_name}
        return self.call('packages', 'getInstallationLinks', params)

    def get_packages(self, company_id: Optional[str] = None) -> Iterator['Package']:
        '''Returns the list of available packages.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
        '''
        params = {'companyId': company_id}
        return self.paginate('packages', 'getPackagesList', params)

    def get_package(self, package_id: str):
        '''Retrieves information about the configuration of a specific
        package.
        '''
        params = {'packageId': package_id}
        return self.call('packages', 'getPackageDetails', params)

    def create_package(self,
        company_id:   str,
        package_name: str,
    ):
        """
        Creates a security package with the specified configuration.

        Args:
            company_id (str): The ID of the company for which the package is being created.
            package_name (str): The name of the package.

        Returns:
            Response from the 'createPackage' API call.
        """
        params = {
                    "companyId": company_id,
                    "packageName": package_name,
                    "description": f'{package_name} for company_id {company_id}',
                    "scanMode": {
                        "type": 2,
                        "computers": {
                            "main": 3
                        },
                        "vms": {
                            "main": 3
                        }
                    }
                }
        return self.call('packages', 'createPackage', params)

    def delete_package(self, package_id: str) -> None:
        params = {'packageId': package_id}
        return self.call('packages', 'deletePackage', params)
# endregion

# region POLICIES
    def get_policies(self, company_id: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        '''Retrieves the list of available policies for a company.

        Args:
            company_id: If not set, the ID of the company linked to the
                API key will be used.
        '''
        params = {'companyId': company_id}
        return self.paginate('policies', 'getPoliciesList', params)

    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        '''Returns all information related to a security policy.
        '''
        params = {'policyId': policy_id}
        return self.call('policies', 'getPolicyDetails', params)

    def export_policies(self, **kwargs):
        raise NotImplementedError

    def import_policies(self, **kwargs):
        raise NotImplementedError
# endregion

# region INTEGRATIONS
# endregion

# region REPORTS
    def get_reports(self, name: str, type: int, only_vm: bool=False) -> Iterator[Dict[str, Any]]:
        '''Returns the list of scheduled reports, according to the
        parameters received.

        Args:
            only_vm: if ``True``, only returns reports for virtual
                machines. Otherwise, reports for computers and virtual
                machines will be returned.
        '''
        service = 'virtualmachines' if only_vm else 'computers'
        params = {'name': name, 'type': type}
        return self.paginate('reports', 'getReportsList', params, service)

    def create_report(self, **kwargs) -> Any:
        raise NotImplementedError

    def get_report_links(self, report_id: str) -> Dict[str, Any]:
        '''Returns information regarding the report availability for
        download and the corresponding download links.
        '''
        params = {'reportId': report_id}
        return self.call('reports', 'getDownloadLinks', params)

    def delete_report(self, report_id: str) -> bool:
        params = {'reportId': report_id}
        return self.call('reports', 'deleteReport', params)
# endregion

# region PUSH
    def set_push_settings(
        self,
        url:          str,
        auth:         str = 'MUST',
        enabled:      bool = True,
        service:      'Literal["jsonRPC", "splunk", "cef"]' = 'jsonRPC',
        validate_ssl: bool = True,
        companies:    Optional[List[str]] = None,
    ) -> bool:
        '''Sets the push event settings.

        Args:
            enabled: Service status.
            service: Type of the web service. Valid values: ``jsonRPC``,
                ``splunk`` and ``cef``.
            url: The web service URL.
            validate_ssl: Whether to validate the SSL certificate of the
                web service.
            auth: Authorization header.
            event_types: Event types to be sent to the web service.
            {
                "hwid-change": true,
                "modules": true,
                "sva": true,
                "registration": true,
                "supa-update-status": true,
                "av": true,
                "aph": true,
                "fw": true,
                "avc": true,
                "uc": true,
                "dp": true,
                "sva-load": true,
                "task-status": true,
                "exchange-malware": true,
                "network-sandboxing": true,
                "adcloud": true,
                "exchange-user-credentials": true,
                "hd": false,
                "antiexploit": true,
                "endpoint-moved-out": true,
                "endpoint-moved-in": true,
                "troubleshooting-activity": true,
                "uninstall": true,
                "install": true,
                "new-incident": true,
                "network-monitor": true,
                "ransomware-mitigation": true,
                "security-container-update-available": true,
                "partner-changed": true,
                "device-control": false
            }
            companies: Companies under your management for which you
                want to receive the events (you need to mention your own
                company as well). If not set, you will receive events
                for all companies you manage.
        '''
        auth_key = 'splunkAuthorization' if service == 'splunk' else 'authorization'

        params = {
            'status':                         int(enabled),
            'serviceType':                    service,
            'serviceSettings': {
                'url':                        url,
                'requireValidSslCertificate': validate_ssl,
                auth_key:                     auth,
            },
            'subscribeToEventTypes':
                {
                    "hwid-change": True,
                    "modules": True,
                    "sva": True,
                    "registration": True,
                    "supa-update-status": True,
                    "av": True,
                    "aph": True,
                    "fw": True,
                    "avc": True,
                    "uc": True,
                    "dp": True,
                    "sva-load": True,
                    "task-status": True,
                    "exchange-malware": True,
                    "network-sandboxing": True,
                    "adcloud": True,
                    "exchange-user-credentials": True,
                    "hd": True,
                    "antiexploit": True,
                    "endpoint-moved-out": True,
                    "endpoint-moved-in": True,
                    "troubleshooting-activity": True,
                    "uninstall": True,
                    "install": True,
                    "new-incident": True,
                    "network-monitor": True,
                    "ransomware-mitigation": True,
                    "security-container-update-available": True,
                    "partner-changed": True,
                    "device-control": True
                }
            ,
            'subscribeToCompanies':           companies or None,
        }

        return self.call('push', 'setPushEventSettings', params)

    def get_push_settings(self):
        params = {}
        return self.call('push', 'getPushEventSettings', params)
    
    def test_push_event(self,
        eventType:  str = "av",
        data: dict = {"malware_name": "Test malware name"}
    ):
        event_list = ["hwid-change","modules","sva","registration","supa-update-status","av","aph","fw","avc","uc","dp","sva-load","task-status","exchange-malware","network-sandboxing","adcloud","exchange-user-credentials","hd","antiexploit","endpoint-moved-out","endpoint-moved-in","troubleshooting-activity","uninstall","install","new-incident","network-monitor","ransomware-mitigation","security-container-update-available","partner-changed","device-control"]
            # Validate the eventType
        if eventType not in event_list:
            raise ValueError(f"Invalid eventType: {eventType}. Must be one of {event_list}.")

        params = {
           "eventType": eventType,
           "data": data
        }
        return self.call('push', 'sendTestPushEvent', params)

# endregion

# region INCIDENTS
# endregion

# region MAINTENANCE WINDOWS (maintenanceWindows)
    def get_maintenance_windows(self, company_id: Optional[str] = None) -> Any:
        raise NotImplementedError

    def get_maintenance_window(self, id: str) -> Any:
        raise NotImplementedError

    def create_maintenance_window(self, **kwargs):
        raise NotImplementedError

    def update_maintenance_window(self, **kwargs):
        raise NotImplementedError

    def delete_maintenance_window(self, **kwargs):
        raise NotImplementedError

    def assign_maintenance_window(self, **kwargs):
        raise NotImplementedError

    def unassign_maintenance_window(self, **kwargs):
        raise NotImplementedError
# endregion

# region QUARANTINE
# endregion

# region GENERAL
    def get_api_key_details(self):
        return self.call('general', 'getApiKeyDetails', {})
# endregion
