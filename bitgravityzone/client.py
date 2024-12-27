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
    ):
        body = {'id': 1, 'jsonrpc': '2.0', 'method': method, 'params': params}
        path = '/'.join(filter(None, (endpoint, service)))
        resp = self.client.post(path, json=body)
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

    def create_account(
        self,
        email:      str,
        profile:    Dict[str, str],
        password:   Optional[str] = None,
        company_id: Optional[str] = None,
        role:       AccountRole = 1,
        rights:     Optional[Dict[str, bool]] = None,
        target_ids: List[str] = None,
    ) -> str:
        '''Creates a user account with password and returns its ID.

        Args:
            email: The email address for the new account.
        '''
        if role == AccountRole.CUSTOM and rights is None:
            raise ValueError('For custom role, rights must be specified.')

        params = {k: v for k, v in {
            'email':     email,
            'profile':   profile,
            'password':  password,
            'companyId': company_id,
            'role':      role,
            'rights':    rights,
            'targetIds': target_ids,
        }.items() if v is not None}

        return self.call('accounts', 'createAccount', params)

    def update_account(self, **kwargs):
        raise NotImplementedError

    def delete_account(self, account_id: str) -> None:
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
        companyType:       int = 1, 
        licenseType:       int = 3,
        assignedProductType: int = 0,
        manageRemoteEnginesScanning: bool = True,
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
            licenseType (int): The type of license (default: 3 for Monthly subscription).
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
        params = {
            'type':                companyType,
            'name':                name,
            'address':             address,
            'phone':               phone,
            'canBeManagedByAbove': managed_by_partner,
            "licenseSubscription": {
                        "type": licenseType, 
                        # "endSubscription": endSubscription,
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

    def get_endpoints(self, **kwargs):
        params = {}
        return self.call('network', 'getEndpointsList', params)

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

    def create_package(self, **kwargs):
        raise NotImplementedError

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
        enabled:      bool,
        service:      'Literal["jsonRPC", "splunk", "cef"]',
        url:          str,
        validate_ssl: bool,
        auth:         str,
        event_types:  List[str],
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
            'subscribeToEventTypes':          event_types,
            'subscribeToCompanies':           companies or None,
        }

        return self.call('push', 'setPushEventSettings', params)
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
