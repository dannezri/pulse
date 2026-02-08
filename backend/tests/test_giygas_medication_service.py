"""
Tests unitaires pour GiygasMedicationService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Ajouter le répertoire parent au path pour importer le service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from giygas_medication_service import GiygasMedicationService


class TestGiygasMedicationService:
    """Tests pour le service Giygas Medications"""
    
    @pytest.fixture
    def service(self):
        """Fixture pour créer une instance du service"""
        return GiygasMedicationService(supabase_client=None)
    
    @pytest.fixture
    def mock_supabase(self):
        """Fixture pour mocker Supabase"""
        mock = Mock()
        mock.client = Mock()
        return mock
    
    # ============================================
    # TESTS : parse_gtin_to_cip13()
    # ============================================
    
    def test_parse_gtin_14_to_cip13(self, service):
        """Test conversion GTIN-14 → CIP13"""
        gtin = "34009300015517"
        expected = "3400930001551"
        
        result = service.parse_gtin_to_cip13(gtin)
        
        assert result == expected, f"Attendu {expected}, reçu {result}"
    
    def test_parse_gtin_13_to_cip13(self, service):
        """Test conversion GTIN-13 → CIP13 (déjà au bon format)"""
        gtin = "3400930001551"
        expected = "3400930001551"
        
        result = service.parse_gtin_to_cip13(gtin)
        
        assert result == expected
    
    def test_parse_gtin_with_spaces(self, service):
        """Test GTIN avec espaces"""
        gtin = "3400 9300 01551 7"
        expected = "3400930001551"
        
        result = service.parse_gtin_to_cip13(gtin)
        
        assert result == expected
    
    def test_parse_gtin_invalid_length(self, service):
        """Test GTIN longueur invalide"""
        gtin = "12345"
        
        result = service.parse_gtin_to_cip13(gtin)
        
        assert result is None
    
    def test_parse_gtin_empty(self, service):
        """Test GTIN vide"""
        result = service.parse_gtin_to_cip13("")
        assert result is None
        
        result = service.parse_gtin_to_cip13(None)
        assert result is None
    
    # ============================================
    # TESTS : search_medications()
    # ============================================
    
    @patch('giygas_medication_service.requests.get')
    def test_search_medications_success(self, mock_get, service):
        """Test recherche médicaments réussie"""
        # Mock réponse API Giygas
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "cis": "60001551",
                "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
                "formePharmaceutique": "comprimé",
                "composition": [
                    {
                        "substanceActive": "PARACETAMOL",
                        "dosage": "500",
                        "unite": "mg"
                    }
                ],
                "presentation": [
                    {
                        "titulaire": "OPELLA HEALTHCARE FRANCE SAS"
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response
        
        # Exécuter recherche
        results = service.search_medications("doliprane")
        
        # Vérifications
        assert len(results) == 1
        assert results[0]["cis"] == "60001551"
        assert results[0]["name"] == "DOLIPRANE 500 mg, comprimé"
        assert results[0]["form"] == "comprimé"
        assert results[0]["active_substance"] == "PARACETAMOL"
        assert results[0]["laboratory"] == "OPELLA HEALTHCARE FRANCE SAS"
        assert results[0]["source"] == "giygas"
    
    def test_search_medications_query_too_short(self, service):
        """Test recherche avec query trop courte"""
        results = service.search_medications("d")
        assert results == []
        
        results = service.search_medications("")
        assert results == []
    
    @patch('giygas_medication_service.requests.get')
    def test_search_medications_api_error(self, mock_get, service):
        """Test recherche avec erreur API"""
        mock_get.side_effect = Exception("API Error")
        
        results = service.search_medications("doliprane")
        
        assert results == []
    
    @patch('giygas_medication_service.requests.get')
    def test_search_medications_404(self, mock_get, service):
        """Test recherche avec 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        results = service.search_medications("medicamentinexistant")
        
        assert results == []
    
    # ============================================
    # TESTS : get_by_cis()
    # ============================================
    
    @patch('giygas_medication_service.requests.get')
    def test_get_by_cis_success(self, mock_get, service):
        """Test récupération par CIS réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cis": "60001551",
            "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
            "formePharmaceutique": "comprimé",
            "composition": [
                {
                    "substanceActive": "PARACETAMOL",
                    "dosage": "500",
                    "unite": "mg"
                }
            ],
            "generiques": [],
            "presentation": [
                {
                    "cip13": "3400930001551",
                    "cip7": "3000155",
                    "libelle": "plaquette(s) de 16 comprimé(s)",
                    "prix": 2.50,
                    "tauxRemboursement": 65,
                    "titulaire": "OPELLA HEALTHCARE FRANCE SAS"
                }
            ],
            "conditions": {
                "prescription": "Liste I"
            }
        }
        mock_get.return_value = mock_response
        
        result = service.get_by_cis("60001551")
        
        assert result is not None
        assert result["cis"] == "60001551"
        assert result["name"] == "DOLIPRANE 500 mg, comprimé"
        assert len(result["composition"]) == 1
        assert result["composition"][0]["substance"] == "PARACETAMOL"
        assert len(result["presentations"]) == 1
        assert result["presentations"][0]["cip13"] == "3400930001551"
        assert result["presentations"][0]["price"] == 2.50
    
    @patch('giygas_medication_service.requests.get')
    def test_get_by_cis_not_found(self, mock_get, service):
        """Test récupération CIS inexistant"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = service.get_by_cis("99999999")
        
        assert result is None
    
    # ============================================
    # TESTS : _normalize_medication_full()
    # ============================================
    
    def test_normalize_medication_full(self, service):
        """Test normalisation données API complètes"""
        api_data = {
            "cis": "60001551",
            "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
            "formePharmaceutique": "comprimé",
            "composition": [
                {
                    "substanceActive": "PARACETAMOL",
                    "dosage": "500",
                    "unite": "mg"
                }
            ],
            "generiques": [
                {
                    "cis": "61234567",
                    "elementPharmaceutique": "PARACETAMOL 500mg générique",
                    "titulaire": "BIOGARAN"
                }
            ],
            "presentation": [
                {
                    "cip13": "3400930001551",
                    "cip7": "3000155",
                    "libelle": "plaquette(s) de 16 comprimé(s)",
                    "prix": 2.50,
                    "tauxRemboursement": 65,
                    "statut": "Commercialisée",
                    "titulaire": "OPELLA HEALTHCARE"
                }
            ],
            "conditions": {
                "prescription": "Liste I"
            }
        }
        
        result = service._normalize_medication_full(api_data)
        
        assert result["cis"] == "60001551"
        assert result["name"] == "DOLIPRANE 500 mg, comprimé"
        assert result["form"] == "comprimé"
        assert result["active_substance"] == "PARACETAMOL"
        assert result["laboratory"] == "OPELLA HEALTHCARE"
        assert len(result["composition"]) == 1
        assert len(result["generics"]) == 1
        assert len(result["presentations"]) == 1
        assert result["conditions"]["prescription"] == "Liste I"
        assert result["source"] == "giygas"
    
    def test_normalize_medication_empty(self, service):
        """Test normalisation données vides"""
        result = service._normalize_medication_full(None)
        assert result is None
        
        result = service._normalize_medication_full({})
        assert result is None
    
    # ============================================
    # TESTS : Cache local
    # ============================================
    
    def test_search_local_cache_no_supabase(self, service):
        """Test cache local sans Supabase"""
        results = service._search_local_cache("doliprane")
        assert results == []
    
    def test_cache_medication_no_supabase(self, service):
        """Test cache médicament sans Supabase"""
        result = service._cache_medication({}, {"cis": "60001551", "name": "Test"})
        assert result is None
    
    @patch('giygas_medication_service.GiygasMedicationService._cache_medication')
    def test_cache_called_on_search(self, mock_cache, service):
        """Test que le cache est appelé lors de la recherche"""
        with patch('giygas_medication_service.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "cis": "60001551",
                    "elementPharmaceutique": "DOLIPRANE 500 mg",
                    "formePharmaceutique": "comprimé",
                    "composition": [{"substanceActive": "PARACETAMOL"}],
                    "presentation": []
                }
            ]
            mock_get.return_value = mock_response
            
            service.search_medications("doliprane")
            
            # Vérifier que _cache_medication a été appelé
            assert mock_cache.called


# ============================================
# TESTS D'INTÉGRATION (nécessitent API Giygas)
# ============================================

@pytest.mark.integration
class TestGiygasIntegration:
    """Tests d'intégration avec API Giygas réelle"""
    
    @pytest.fixture
    def service(self):
        return GiygasMedicationService(supabase_client=None)
    
    def test_search_real_api(self, service):
        """Test recherche avec API réelle"""
        results = service.search_medications("doliprane")
        
        # Vérifications basiques
        assert isinstance(results, list)
        if len(results) > 0:
            assert "cis" in results[0]
            assert "name" in results[0]
            assert "source" in results[0]
            assert results[0]["source"] == "giygas"
    
    def test_get_by_cis_real_api(self, service):
        """Test récupération CIS avec API réelle"""
        # CIS du Doliprane 500mg
        result = service.get_by_cis("60001551")
        
        if result:
            assert result["cis"] == "60001551"
            assert "composition" in result
            assert "presentations" in result


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])
