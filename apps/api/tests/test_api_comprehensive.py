import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure apps/api is in the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_root = os.path.abspath(os.path.join(current_dir, '../../api'))
sys.path.append(api_root)

from app.main import app

client = TestClient(app)

# Helper to get a valid practice GUID for subsequent tests
def get_first_practice_guid():
    response = client.get("/api/practices/list")
    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            # Prefer practiceGuid, fallback to locationGuid as seen in frontend logic
            return data[0].get("practiceGuid") or data[0].get("locationGuid")
    return None

class TestPractices:
    def test_get_practices_list(self):
        response = client.get("/api/practices/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "city" in data[0]
            assert "encounterCount" in data[0]

class TestPatients:
    practice_guid = get_first_practice_guid()

    def test_get_patients_list(self):
        if not self.practice_guid:
            pytest.skip("No practices found to test patients")
        
        response = client.get(f"/api/practices/{self.practice_guid}/patients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "patientGuid" in data[0]
            assert "name" in data[0]

    def test_get_patient_details(self):
        if not self.practice_guid:
            pytest.skip("No practices found")
        
        # Get a patient first
        list_resp = client.get(f"/api/practices/{self.practice_guid}/patients")
        patients = list_resp.json()
        if not patients:
            pytest.skip("No patients found in practice")
            
        patient_guid = patients[0]["patientGuid"]
        response = client.get(f"/api/patients/{patient_guid}/details")
        assert response.status_code == 200
        data = response.json()
        assert "patient" in data
        assert "insurance" in data
        assert "encounters" in data

class TestEncounters:
    practice_guid = get_first_practice_guid()

    def test_get_encounters_list(self):
        if not self.practice_guid:
            pytest.skip("No practices found")
        
        response = client.get(f"/api/practices/{self.practice_guid}/encounters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "encounterId" in data[0]
            assert "status" in data[0]

class TestClaims:
    practice_guid = get_first_practice_guid()

    def test_get_claims_list(self):
        if not self.practice_guid:
            pytest.skip("No practices found")
        
        response = client.get(f"/api/practices/{self.practice_guid}/claims")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "claimId" in data[0]
            assert "billed" in data[0]
            assert "status" in data[0]

class TestERA:
    def test_get_eras_list(self):
        response = client.get("/api/eras/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "totalPaid" in data[0]
            assert "payer" in data[0]

    def test_get_era_details(self):
        # Get a list first
        list_resp = client.get("/api/eras/list")
        eras = list_resp.json()
        if not eras:
            pytest.skip("No ERAs found")
            
        era_id = eras[0]["id"]
        response = client.get(f"/api/eras/{era_id}/details")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "bundles" in data

class TestAnalytics:
    practice_guid = get_first_practice_guid()

    def test_global_dashboard_metrics(self):
        response = client.get("/api/dashboard/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "totalEncounters" in data

    def test_global_performance_summary(self):
         response = client.get("/api/v1/analytics/global/performance-summary")
         assert response.status_code == 200
         data = response.json()
         assert "practice_name" in data
         assert "total_claims" in data

    def test_financial_metrics(self):
        if not self.practice_guid:
             pytest.skip("No practice found for metrics")

        response = client.get(f"/api/practices/{self.practice_guid}/financial-metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "comparisons" in data
