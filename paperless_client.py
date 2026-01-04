import requests

class PaperlessClient:

    api_url: str
    headers: dict[str, str]

    def __init__(self, paperless_url: str, api_token: str):
        self.api_url = paperless_url.rstrip('/') # Remove trailing slash if any
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Accept': 'application/json; version=2'
        }

    def _get_full_url(self, endpoint: str) -> str:
        return f"{self.api_url}/api/{endpoint}/"

    def check_connection(self):
        try:
            response = requests.get(self._get_full_url('correspondents'), headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def get_correspondents(self):
        return self._get_all_pages('correspondents')

    def get_document_types(self):
        return self._get_all_pages('document_types')

    def _get_all_pages(self, endpoint: str) -> list[dict]:
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

    def bulk_edit_correspondent(self, document_ids: list[int], new_correspondent_id: int):
        if not document_ids:
            return
        
        # Chunking to avoid too large payloads
        chunk_size = 100
        for i in range(0, len(document_ids), chunk_size):
            chunk = document_ids[i:i + chunk_size]
            url = self._get_full_url('documents/bulk_edit')
            payload = {
                "documents": chunk,
                "method": "set_correspondent",
                "parameters": {"correspondent": new_correspondent_id}
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

    def bulk_edit_document_type(self, document_ids: list[int], new_dtype_id: int):
        if not document_ids:
            return
            
        chunk_size = 100
        for i in range(0, len(document_ids), chunk_size):
            chunk = document_ids[i:i + chunk_size]
            url = self._get_full_url('documents/bulk_edit')
            payload = {
                "documents": chunk,
                "method": "set_document_type",
                "parameters": {"document_type": new_dtype_id}
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

    def delete_correspondent(self, correspondent_id: int):
        url = self._get_full_url(f'correspondents/{correspondent_id}')
        # Remove trailing slash for ID resource if needed, but usually DRF handles it.
        # Actually DRF usually expects slash at end.
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

    def delete_document_type(self, dtype_id: int):
        url = self._get_full_url(f'document_types/{dtype_id}')
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
