import requests

class PaperlessClient:
    """Client for interacting with the Paperless API."""

    api_url: str
    headers: dict[str, str]

    def __init__(self, paperless_url: str, api_token: str):
        """Initialize the PaperlessClient with API URL and token.
        Args:
            paperless_url (str): Base URL of the Paperless API
            api_token (str): API token for authentication
        """
        self.api_url = paperless_url.rstrip('/') # Remove trailing slash if any
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Accept': 'application/json; version=2'
        }

    def _get_full_url(self, endpoint: str) -> str:
        """Gets the full URL including the endpoint

        Args:
            endpoint (str): The desired endpoint (correspondents / document_types)

        Returns:
            str: The full URL
        """
        return f"{self.api_url}/api/{endpoint}/"

    def check_connection(self) -> bool:
        """Check if the API is reachable with the current settings.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            response = requests.get(self._get_full_url('correspondents'), headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def get_correspondents(self) -> list[dict]:
        """Retrieve all correspondents from the API.

        Returns:
            list[dict]: A list of correspondent objects.
        """
        return self._get_all_pages('correspondents')

    def get_document_types(self) -> list[dict]:
        """Retrieve all document types from the API.
        
        Returns:
            list[dict]: A list of document type objects.
        """
        return self._get_all_pages('document_types')

    def _get_all_pages(self, endpoint: str) -> list[dict]:
        """Retrieve all pages of results from a paginated API endpoint.
        
        Args:
            endpoint (str): The API endpoint to query.
        
        Returns:
            list[dict]: A list of all items retrieved from the endpoint.
        """
        results = []
        url = self._get_full_url(endpoint)
        while url:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get('results', []))
            url = data.get('next')
        return results

    def get_documents_by_correspondent(self, correspondent_id: int) -> list[dict]:
        """Retrieve documents filtered by correspondent ID.
        Args:
            correspondent_id (int): The ID of the correspondent to filter by.
        Returns:
            list[dict]: A list of document objects.
        """

        # Paperless-ngx filtering usually works via query params
        # ?correspondent__id=X
        url = self._get_full_url('documents')
        params = {'correspondent__id': correspondent_id}
        results = []

        while url:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get('results', []))
            url = data.get('next')
            params = {} # params only needed for first call if next url contains them
        return results

    def get_documents_by_document_type(self, dtype_id: int) -> list[dict]:
        """Retrieve documents filtered by document type ID.
        Args:
            dtype_id (int): The ID of the document type to filter by.
        Returns:
            list[dict]: A list of document objects.
        """
        # Paperless-ngx filtering usually works via query params
        # ?document_type__id=X
        url = self._get_full_url('documents')
        params = {'document_type__id': dtype_id}
        results = []

        while url:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get('results', []))
            url = data.get('next')
            params = {}
        return results

    def get_document_titles(self, item_type: str, item_id: int) -> list[dict]:
        """Retrieve document titles for documents linked to a specific
        correspondent or document type.
        Args:
            item_type (str): Either 'correspondent' or 'document_type'.
            item_id (int): The ID of the correspondent or document type.
        Returns:
            list[dict]: A list of document titles and IDs.
        """
        if item_type == 'correspondent':
            docs = self.get_documents_by_correspondent(item_id)
        elif item_type == 'document_type':
            docs = self.get_documents_by_document_type(item_id)
        else:
            return []
        
        return [{'id': doc.get('id'), 'title': doc.get('title', 'Unknown')} for doc in docs]

    def bulk_edit_correspondent(self, document_ids: list[int], new_correspondent_id: int):
        """Bulk edit documents to set a new correspondent.

        Args:
            document_ids (list[int]): List of document IDs to update.
            new_correspondent_id (int): The new correspondent ID to set.

        Raises:
            requests.HTTPError: If the API request fails.
        """

        # Do nothing if there are no documents to update
        if not document_ids:
            return
        
        # Chunking to avoid too large payloads
        chunk_size = 100
        for i in range(0, len(document_ids), chunk_size):
            chunk = document_ids[i:i + chunk_size]
            url = self._get_full_url('documents/bulk_edit')

            # Create the payload according to Paperless API spec
            # https://docs.paperless-ngx.com/api/#documents
            payload = {
                "documents": chunk,
                "method": "set_correspondent",
                "parameters": {"correspondent": new_correspondent_id}
            }

            # Send the POST request and Raise an error if the request failed
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

    def bulk_edit_document_type(self, document_ids: list[int], new_dtype_id: int):
        """Bulk edit documents to set a new document type.
        Args:
            document_ids (list[int]): List of document IDs to update.
            new_dtype_id (int): The new document type ID to set.
        Raises:
            requests.HTTPError: If the API request fails.
        """
        # Do nothing if there are no documents to update
        if not document_ids:
            return
            
        # Chunking to avoid too large payloads
        chunk_size = 100
        for i in range(0, len(document_ids), chunk_size):
            chunk = document_ids[i:i + chunk_size]
            url = self._get_full_url('documents/bulk_edit')

            # Create the payload according to Paperless API spec
            # https://docs.paperless-ngx.com/api/#documents
            payload = {
                "documents": chunk,
                "method": "set_document_type",
                "parameters": {"document_type": new_dtype_id}
            }

            # Send the POST request and Raise an error if the request failed
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

    def delete_correspondent(self, correspondent_id: int):
        """Delete a correspondent by ID.
        Args:
            correspondent_id (int): The ID of the correspondent to delete.
        Raises:
            requests.HTTPError: If the API request fails.
        """
        url = self._get_full_url(f'correspondents/{correspondent_id}')
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

    def delete_document_type(self, dtype_id: int):
        """Delete a document type by ID.
        Args:
            dtype_id (int): The ID of the document type to delete.
        Raises:
            requests.HTTPError: If the API request fails.
        """
        url = self._get_full_url(f'document_types/{dtype_id}')
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
