import httpx

class NomadClient:
    def __init__(self, host: str):
        self.base_url = f"http://{host}:4646"

    def register_job(self, job_def: dict):
        response = httpx.post(f"{self.base_url}/v1/jobs", json=job_def)
        response.raise_for_status()
        return response.json()

    def list_jobs(self):
        response = httpx.get(f"{self.base_url}/v1/jobs")
        response.raise_for_status()
        return response.json()

    def get_job(self, job_id: str):
        response = httpx.get(f"{self.base_url}/v1/job/{job_id}")
        response.raise_for_status()
        return response.json()

    def stop_job(self, job_id: str):
        response = httpx.delete(f"{self.base_url}/v1/job/{job_id}")
        response.raise_for_status()
        return response.json()
