"""
Tests pour le service intraday_energy_service

Teste:
- Classification des événements
- Estimation de l'impact
- Génération de la courbe
- Génération des fenêtres de risque
- Génération des notes
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from intraday_energy_service import (
    classify_event_type,
    estimate_event_impact,
    generate_intraday_curve,
    generate_risk_windows_intraday,
    generate_notes_intraday,
    generate_intraday_forecast,
)


class TestClassifyEventType:
    """Tests pour la classification des événements"""
    
    def test_classify_meeting(self):
        event = {'title': 'Réunion client', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'meeting'
        assert 'meeting' in tags
    
    def test_classify_sport(self):
        event = {'title': 'Course à pied', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'sport'
        assert 'sport' in tags
    
    def test_classify_travel(self):
        event = {'title': 'Vol Paris-Lyon', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'travel'
        assert 'travel' in tags
    
    def test_classify_focus(self):
        event = {'title': 'Deep work - coding', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'focus'
        assert 'focus' in tags
    
    def test_classify_social(self):
        event = {'title': 'Déjeuner avec Paul', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'social'
        assert 'social' in tags
    
    def test_classify_high_stress_meeting(self):
        event = {'title': 'Réunion client importante', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'meeting'
        assert 'high_stress' in tags or 'high_focus' in tags
    
    def test_classify_unknown(self):
        event = {'title': 'Événement mystère', 'notes': '', 'location': ''}
        event_type, tags = classify_event_type(event)
        assert event_type == 'other'


class TestEstimateEventImpact:
    """Tests pour l'estimation de l'impact des événements"""
    
    def test_meeting_impact(self):
        now = datetime.utcnow()
        event = {
            'title': 'Réunion',
            'start_time': now.isoformat() + 'Z',
            'end_time': (now + timedelta(hours=1)).isoformat() + 'Z',
        }
        impact, confidence = estimate_event_impact(
            event, 'meeting', ['meeting'], 75.0, 0.7, 0.3
        )
        assert impact < 0  # Impact négatif
        assert 0 <= confidence <= 1
    
    def test_sport_impact(self):
        now = datetime.utcnow()
        event = {
            'title': 'Sport',
            'start_time': now.isoformat() + 'Z',
            'end_time': (now + timedelta(hours=1)).isoformat() + 'Z',
        }
        impact, confidence = estimate_event_impact(
            event, 'sport', ['sport'], 75.0, 0.7, 0.3
        )
        assert impact < 0  # Impact négatif immédiat
        assert confidence > 0.6  # Confiance élevée pour sport
    
    def test_long_event_higher_impact(self):
        now = datetime.utcnow()
        event_short = {
            'title': 'Réunion courte',
            'start_time': now.isoformat() + 'Z',
            'end_time': (now + timedelta(minutes=30)).isoformat() + 'Z',
        }
        event_long = {
            'title': 'Réunion longue',
            'start_time': now.isoformat() + 'Z',
            'end_time': (now + timedelta(hours=3)).isoformat() + 'Z',
        }
        
        impact_short, _ = estimate_event_impact(
            event_short, 'meeting', ['meeting'], 75.0, 0.7, 0.3
        )
        impact_long, _ = estimate_event_impact(
            event_long, 'meeting', ['meeting'], 75.0, 0.7, 0.3
        )
        
        assert abs(impact_long) > abs(impact_short)
    
    def test_low_recovery_increases_impact(self):
        now = datetime.utcnow()
        event = {
            'title': 'Réunion',
            'start_time': now.isoformat() + 'Z',
            'end_time': (now + timedelta(hours=1)).isoformat() + 'Z',
        }
        
        impact_good_recovery, _ = estimate_event_impact(
            event, 'meeting', ['meeting'], 75.0, 0.8, 0.3
        )
        impact_bad_recovery, _ = estimate_event_impact(
            event, 'meeting', ['meeting'], 75.0, 0.3, 0.3
        )
        
        assert abs(impact_bad_recovery) > abs(impact_good_recovery)


class TestGenerateIntradayCurve:
    """Tests pour la génération de la courbe intraday"""
    
    @patch('intraday_energy_service.datetime')
    def test_generate_curve_basic(self, mock_datetime):
        # Mock datetime.utcnow() pour contrôler l'heure actuelle
        now = datetime(2026, 1, 30, 9, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        points = generate_intraday_curve(
            user_id='test-user',
            target_date='2026-01-30',
            base_energy=75.0,
            recovery=0.7,
            sleep_debt=0.3,
            overtrain=0.2,
            events=[]
        )
        
        # Vérifier qu'on a des points
        assert len(points) > 0
        
        # Vérifier structure des points
        for point in points:
            assert 't' in point
            assert 'energy' in point
            assert 0 <= point['energy'] <= 100
    
    @patch('intraday_energy_service.datetime')
    def test_curve_decays_during_day(self, mock_datetime):
        now = datetime(2026, 1, 30, 9, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        points = generate_intraday_curve(
            user_id='test-user',
            target_date='2026-01-30',
            base_energy=80.0,
            recovery=0.7,
            sleep_debt=0.3,
            overtrain=0.2,
            events=[]
        )
        
        # Vérifier que l'énergie décroît généralement dans la journée
        # (peut y avoir des variations, mais tendance générale)
        if len(points) >= 3:
            morning_energy = points[0]['energy']
            evening_energy = points[-1]['energy']
            # L'énergie du soir devrait être inférieure ou égale au matin
            assert evening_energy <= morning_energy + 10  # Tolérance de 10


class TestGenerateRiskWindows:
    """Tests pour la génération des fenêtres de risque"""
    
    def test_no_dip(self):
        # Tous les points au-dessus de 70
        points = [
            {'t': '2026-01-30T09:00:00Z', 'energy': 80},
            {'t': '2026-01-30T10:00:00Z', 'energy': 78},
            {'t': '2026-01-30T11:00:00Z', 'energy': 75},
        ]
        windows = generate_risk_windows_intraday(points, [])
        assert len(windows) == 0
    
    def test_detect_dip(self):
        # Creux prolongé
        points = [
            {'t': '2026-01-30T09:00:00Z', 'energy': 80},
            {'t': '2026-01-30T10:00:00Z', 'energy': 65},
            {'t': '2026-01-30T11:00:00Z', 'energy': 60},
            {'t': '2026-01-30T12:00:00Z', 'energy': 62},
            {'t': '2026-01-30T13:00:00Z', 'energy': 75},
        ]
        windows = generate_risk_windows_intraday(points, [])
        assert len(windows) >= 1
        
        # Vérifier structure
        window = windows[0]
        assert 'from' in window
        assert 'to' in window
        assert 'kind' in window
        assert 'label' in window
        assert window['kind'] == 'dip'
    
    def test_short_dip_ignored(self):
        # Creux trop court (< 1h)
        points = [
            {'t': '2026-01-30T09:00:00Z', 'energy': 80},
            {'t': '2026-01-30T09:30:00Z', 'energy': 65},
            {'t': '2026-01-30T10:00:00Z', 'energy': 75},
        ]
        windows = generate_risk_windows_intraday(points, [])
        # Ne devrait pas détecter de creux (durée < 1h)
        assert len(windows) == 0


class TestGenerateNotes:
    """Tests pour la génération des notes"""
    
    def test_low_energy_note(self):
        notes = generate_notes_intraday(
            base_energy=50.0,
            recovery=0.7,
            sleep_debt=0.3,
            events=[],
            windows=[]
        )
        assert len(notes) > 0
        assert any('faible' in note.lower() for note in notes)
    
    def test_high_energy_note(self):
        notes = generate_notes_intraday(
            base_energy=85.0,
            recovery=0.8,
            sleep_debt=0.2,
            events=[],
            windows=[]
        )
        assert len(notes) > 0
        assert any('excellente' in note.lower() or 'bonne' in note.lower() for note in notes)
    
    def test_dip_note(self):
        windows = [{'from': '16:00', 'to': '18:00', 'kind': 'dip', 'label': 'Creux'}]
        notes = generate_notes_intraday(
            base_energy=70.0,
            recovery=0.6,
            sleep_debt=0.4,
            events=[],
            windows=windows
        )
        assert any('creux' in note.lower() for note in notes)
    
    def test_max_3_notes(self):
        # Même avec beaucoup de conditions, max 3 notes
        windows = [{'from': '16:00', 'to': '18:00', 'kind': 'dip', 'label': 'Creux'}]
        events = [
            {
                'title': 'Réunion importante',
                'start_time': '2026-01-30T14:00:00Z',
                'impact': -15,
            }
        ]
        notes = generate_notes_intraday(
            base_energy=50.0,
            recovery=0.3,
            sleep_debt=0.7,
            events=events,
            windows=windows
        )
        assert len(notes) <= 3


class TestGenerateIntradayForecast:
    """Tests d'intégration pour la génération complète"""
    
    @patch('intraday_energy_service.supabase')
    @patch('intraday_energy_service.get_daily_energy')
    @patch('intraday_energy_service.datetime')
    def test_generate_forecast_success(self, mock_datetime, mock_get_daily_energy, mock_supabase):
        # Setup mocks
        now = datetime(2026, 1, 30, 9, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        mock_get_daily_energy.return_value = {
            'energy_score': 0.75,
            'confidence': 0.8,
            'components': {
                'recovery': 0.7,
                'sleep_debt': 0.3,
                'overtrain': 0.2,
                'infection': 0.1
            }
        }
        
        # Mock Supabase response (pas d'événements)
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        
        forecast = generate_intraday_forecast('test-user', '2026-01-30')
        
        # Vérifications
        assert forecast is not None
        assert forecast['type'] == 'intraday_energy'
        assert forecast['date'] == '2026-01-30'
        assert 'points' in forecast
        assert 'windows' in forecast
        assert 'events' in forecast
        assert 'notes' in forecast
        assert 'confidence' in forecast
        assert len(forecast['points']) > 0
    
    @patch('intraday_energy_service.get_daily_energy')
    def test_generate_forecast_no_daily_energy(self, mock_get_daily_energy):
        mock_get_daily_energy.return_value = None
        
        forecast = generate_intraday_forecast('test-user', '2026-01-30')
        
        assert forecast is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
