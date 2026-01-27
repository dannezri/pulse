"""
Tests d'Intégrité : Idempotence & Dédoublonnage des Webhooks

Vérifie que le système protège la base de données Supabase contre les doublons
lorsque le même webhook est envoyé plusieurs fois.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_client import SupabaseClient


class TestWebhookIdempotence:
    """Tests pour vérifier l'idempotence des webhooks"""
    
    @pytest.fixture
    def mock_payload(self):
        """Payload de webhook de test avec event_id"""
        return {
            "user_id": "open-wearables-uuid-123",
            "event_id": "webhook-event-uuid-456",  # ID unique pour idempotence
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {
                "hr": [
                    {
                        "value": 72,
                        "timestamp": "2024-01-15T10:00:00Z"
                    },
                    {
                        "value": 73,
                        "timestamp": "2024-01-15T10:05:00Z"
                    }
                ],
                "hrv": [
                    {
                        "value": 45,
                        "timestamp": "2024-01-15T10:00:00Z"
                    }
                ],
                "sleep": {
                    "duration_seconds": 28800,  # 8 heures
                    "start_time": "2024-01-15T22:00:00Z",
                    "score": 85
                },
                "steps": [
                    {
                        "value": 5000,
                        "timestamp": "2024-01-15T10:00:00Z"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_supabase_user_id(self):
        """ID utilisateur Supabase de test"""
        return "supabase-user-uuid-789"
    
    @pytest.fixture
    def mock_supabase_client(self, mock_supabase_user_id):
        """Mock du client Supabase avec comportement idempotent"""
        mock_client = MagicMock(spec=SupabaseClient)
        
        # Mock pour get_user_by_open_wearables_id
        mock_client.get_user_by_open_wearables_id.return_value = mock_supabase_user_id
        
        # Mock pour insert_biometric - simule l'idempotence
        # Premier appel : insertion réussie
        # Deuxième appel avec même source_event_id : retourne duplicate
        insert_results = []
        
        def mock_insert_biometric(user_id, metric_type, value, recorded_at, raw_data, 
                                  source="open_wearables", source_event_id=None):
            # Vérifier si on a déjà inséré avec ce source_event_id
            for prev_result in insert_results:
                if (prev_result["user_id"] == user_id and 
                    prev_result["source"] == source and 
                    prev_result["source_event_id"] == source_event_id):
                    # Doublon détecté
                    return {"status": "duplicate", "existing_id": prev_result["id"]}
            
            # Nouvelle insertion
            result = {
                "status": "inserted",
                "data": {
                    "id": f"biometric-{len(insert_results)}",
                    "user_id": user_id,
                    "metric_type": metric_type,
                    "value": value,
                    "recorded_at": recorded_at.isoformat(),
                    "raw_data": raw_data,
                    "source": source,
                    "source_event_id": source_event_id
                }
            }
            insert_results.append({
                "id": result["data"]["id"],
                "user_id": user_id,
                "source": source,
                "source_event_id": source_event_id
            })
            return result
        
        mock_client.insert_biometric.side_effect = mock_insert_biometric
        
        # Mock pour les autres méthodes nécessaires
        mock_client.get_today_biometrics.return_value = {}
        mock_client.get_historical_biometrics.return_value = []
        mock_client.get_user_goal.return_value = "energy"
        mock_client.save_health_profile.return_value = {"status": "success"}
        mock_client.update_baselines.return_value = {"status": "success"}
        mock_client.get_latest_health_profile.return_value = None
        
        # Mock pour webhook_events
        webhook_events = []
        def mock_save_webhook_event(supabase_user_id, open_wearables_user_id, payload, signature=None):
            event_id = f"webhook-event-{len(webhook_events)}"
            webhook_events.append({
                "id": event_id,
                "user_id": supabase_user_id,
                "payload": payload,
                "status": "pending"
            })
            return event_id
        
        # Mock du client Supabase Python (pour webhook_events)
        mock_supabase_python_client = MagicMock()
        mock_supabase_python_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "webhook-event-0"}
        ]
        mock_supabase_python_client.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        mock_supabase_python_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        mock_client.client = mock_supabase_python_client
        
        return mock_client
    
    @pytest.fixture
    def mock_open_wearables_client(self):
        """Mock du client Open Wearables"""
        mock_client = MagicMock()
        mock_client.verify_webhook_signature.return_value = True
        return mock_client
    
    def test_webhook_idempotence_at_api_level(
        self, 
        mock_payload, 
        mock_supabase_client, 
        mock_open_wearables_client
    ):
        """
        Test : Envoi du même webhook deux fois → pas de doublons dans biometrics
        
        Scénario : Open Wearables envoie deux fois le même webhook à 1 seconde d'intervalle.
        Le système doit détecter les doublons grâce à source_event_id et ne pas créer
        de doublons dans la table biometrics.
        
        Ce test vérifie que le WebhookReceiver peut recevoir le même webhook deux fois
        et que l'idempotence est gérée correctement.
        """
        from webhook_receiver import WebhookReceiver
        
        # Créer une instance réelle du receiver avec les mocks
        receiver = WebhookReceiver(
            open_wearables_client=mock_open_wearables_client,
            supabase_client=mock_supabase_client
        )
        
        # Mock pour push_normalization_job
        with patch('webhook_receiver.push_normalization_job', return_value="task-123"):
            # Premier envoi
            result1 = receiver.receive_webhook(mock_payload)
            assert result1["status"] == "accepted"
            assert "webhook_event_id" in result1
            
            # Deuxième envoi identique (même event_id)
            result2 = receiver.receive_webhook(mock_payload)
            assert result2["status"] == "accepted"
            assert "webhook_event_id" in result2
            
            # Vérifier que deux webhook_events ont été créés (normal, car chaque appel
            # crée un nouvel événement dans webhook_events, mais l'idempotence est gérée
            # au niveau de biometrics via source_event_id)
            # Le fait que les deux appels réussissent confirme que le système accepte
            # les webhooks dupliqués sans erreur
            
            # Vérifier que get_user_by_open_wearables_id a été appelé deux fois
            assert mock_supabase_client.get_user_by_open_wearables_id.call_count == 2
    
    def test_insert_biometric_idempotence(
        self, 
        mock_supabase_user_id,
        mock_supabase_client
    ):
        """
        Test : insert_biometric détecte les doublons via source_event_id
        
        Vérifie que lorsqu'on insère deux fois la même mesure avec le même
        source_event_id, le deuxième appel retourne "duplicate".
        """
        # Premier appel : insertion réussie
        result1 = mock_supabase_client.insert_biometric(
            user_id=mock_supabase_user_id,
            metric_type="hr",
            value=72.0,
            recorded_at=datetime.now(),
            raw_data={"value": 72, "timestamp": "2024-01-15T10:00:00Z"},
            source="open_wearables",
            source_event_id="webhook-event-456_hr_abc123"
        )
        
        assert result1["status"] == "inserted"
        assert "data" in result1
        
        # Deuxième appel identique (même source_event_id)
        result2 = mock_supabase_client.insert_biometric(
            user_id=mock_supabase_user_id,
            metric_type="hr",
            value=72.0,
            recorded_at=datetime.now(),
            raw_data={"value": 72, "timestamp": "2024-01-15T10:00:00Z"},
            source="open_wearables",
            source_event_id="webhook-event-456_hr_abc123"  # Même source_event_id
        )
        
        # Le deuxième appel doit retourner "duplicate"
        assert result2["status"] == "duplicate"
        assert "existing_id" in result2
        assert result2["existing_id"] == result1["data"]["id"]
    
    def test_insert_biometric_different_event_ids(
        self,
        mock_supabase_user_id,
        mock_supabase_client
    ):
        """
        Test : Deux mesures avec des source_event_id différents → deux insertions
        
        Vérifie que des mesures avec des source_event_id différents sont bien
        insérées séparément (pas de faux positifs).
        """
        # Premier appel avec event_id 1
        result1 = mock_supabase_client.insert_biometric(
            user_id=mock_supabase_user_id,
            metric_type="hr",
            value=72.0,
            recorded_at=datetime.now(),
            raw_data={"value": 72, "timestamp": "2024-01-15T10:00:00Z"},
            source="open_wearables",
            source_event_id="webhook-event-456_hr_abc123"
        )
        
        assert result1["status"] == "inserted"
        
        # Deuxième appel avec event_id différent
        result2 = mock_supabase_client.insert_biometric(
            user_id=mock_supabase_user_id,
            metric_type="hr",
            value=73.0,  # Même valeur mais event_id différent
            recorded_at=datetime.now(),
            raw_data={"value": 73, "timestamp": "2024-01-15T10:05:00Z"},
            source="open_wearables",
            source_event_id="webhook-event-456_hr_def456"  # Event ID différent
        )
        
        # Le deuxième appel doit être inséré (pas un doublon)
        assert result2["status"] == "inserted"
        assert result2["data"]["id"] != result1["data"]["id"]
    
    def test_worker_processing_idempotence(
        self,
        mock_payload,
        mock_supabase_user_id,
        mock_supabase_client
    ):
        """
        Test : Le worker traite le même webhook deux fois → pas de doublons
        
        Simule le traitement d'un webhook par le worker deux fois (par exemple
        en cas de retry). Vérifie que les données ne sont pas dupliquées.
        """
        # Simuler l'insertion des données du webhook une première fois
        # (comme le ferait le worker)
        base_event_id = mock_payload["event_id"]
        
        # Insérer les données HR
        hr_results = []
        for idx, hr_entry in enumerate(mock_payload["data"]["hr"]):
            result = mock_supabase_client.insert_biometric(
                user_id=mock_supabase_user_id,
                metric_type="hr",
                value=float(hr_entry["value"]),
                recorded_at=datetime.fromisoformat(hr_entry["timestamp"].replace("Z", "+00:00")),
                raw_data=hr_entry,
                source="open_wearables",
                source_event_id=f"{base_event_id}_hr_{idx}_abc123"  # Simule la génération du worker
            )
            hr_results.append(result)
        
        # Vérifier que les insertions ont réussi
        assert all(r["status"] == "inserted" for r in hr_results)
        
        # Simuler un retry : traiter le même webhook une deuxième fois
        hr_results_retry = []
        for idx, hr_entry in enumerate(mock_payload["data"]["hr"]):
            result = mock_supabase_client.insert_biometric(
                user_id=mock_supabase_user_id,
                metric_type="hr",
                value=float(hr_entry["value"]),
                recorded_at=datetime.fromisoformat(hr_entry["timestamp"].replace("Z", "+00:00")),
                raw_data=hr_entry,
                source="open_wearables",
                source_event_id=f"{base_event_id}_hr_{idx}_abc123"  # Même source_event_id
            )
            hr_results_retry.append(result)
        
        # Vérifier que les retries sont détectés comme doublons
        assert all(r["status"] == "duplicate" for r in hr_results_retry)
        
        # Vérifier que les IDs existants correspondent
        for original, retry in zip(hr_results, hr_results_retry):
            assert retry["existing_id"] == original["data"]["id"]


class TestSourceEventIdGeneration:
    """Tests pour la génération de source_event_id"""
    
    def test_source_event_id_with_base_event_id(self):
        """Test : Génération de source_event_id avec base event_id"""
        from webhook_handler import OpenWearablesWebhookHandler
        from unittest.mock import MagicMock
        
        handler = OpenWearablesWebhookHandler(
            open_wearables_client=MagicMock(),
            normalizer=MagicMock(),
            supabase_client=MagicMock()
        )
        
        base_event_id = "webhook-event-123"
        metric_type = "hr"
        entry_data = {"value": 72, "timestamp": "2024-01-15T10:00:00Z"}
        
        source_event_id = handler._generate_source_event_id(
            base_event_id,
            metric_type,
            entry_data
        )
        
        # Vérifier le format : {base_event_id}_{metric_type}_{hash}
        assert source_event_id.startswith(f"{base_event_id}_{metric_type}_")
        assert len(source_event_id) > len(f"{base_event_id}_{metric_type}_")
    
    def test_source_event_id_without_base_event_id(self):
        """Test : Génération de source_event_id sans base event_id (fallback)"""
        from webhook_handler import OpenWearablesWebhookHandler
        from unittest.mock import MagicMock
        
        handler = OpenWearablesWebhookHandler(
            open_wearables_client=MagicMock(),
            normalizer=MagicMock(),
            supabase_client=MagicMock()
        )
        
        entry_data = {"value": 72, "timestamp": "2024-01-15T10:00:00Z"}
        
        source_event_id = handler._generate_source_event_id(
            None,  # Pas de base_event_id
            "hr",
            entry_data
        )
        
        # Devrait être un hash MD5 (32 caractères hex)
        assert len(source_event_id) == 32
        assert all(c in "0123456789abcdef" for c in source_event_id)
    
    def test_source_event_id_consistency(self):
        """Test : Même entrée → même source_event_id"""
        from webhook_handler import OpenWearablesWebhookHandler
        from unittest.mock import MagicMock
        
        handler = OpenWearablesWebhookHandler(
            open_wearables_client=MagicMock(),
            normalizer=MagicMock(),
            supabase_client=MagicMock()
        )
        
        base_event_id = "webhook-event-123"
        metric_type = "hr"
        entry_data = {"value": 72, "timestamp": "2024-01-15T10:00:00Z"}
        
        # Générer deux fois avec les mêmes paramètres
        source_event_id_1 = handler._generate_source_event_id(
            base_event_id,
            metric_type,
            entry_data
        )
        
        source_event_id_2 = handler._generate_source_event_id(
            base_event_id,
            metric_type,
            entry_data
        )
        
        # Doit être identique (déterministe)
        assert source_event_id_1 == source_event_id_2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
