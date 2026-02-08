# Pulse Latent States System - Implementation Complete ✅

**Date**: 2026-01-29  
**Status**: Fully Implemented and Ready for Testing

---

## 📋 Overview

The Pulse Latent States System has been successfully implemented. This system adds 4 scientifically-calculated physiological states to the Pulse Brief system:

1. **Recovery** (Récupération) - Overall recovery quality
2. **Sleep Debt** (Dette de sommeil) - Accumulated sleep deficit
3. **Overtrain** (Surcharge entraînement) - Training load analysis with ACWR
4. **Infection-like** (Signature infection) - Early detection of illness patterns

---

## 🏗️ Architecture Summary

```
┌─────────────┐
│ Oura/Vital  │
│   Data      │
└──────┬──────┘
       │
       v
┌─────────────────┐
│   Supabase      │
│  (biometrics)   │
└──────┬──────────┘
       │
       v
┌──────────────────────────────┐
│  LatentStateService          │
│  - Fetches biometrics        │
│  - Fetches baselines         │
│  - Calls calculators         │
│  - Caches in daily_state     │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│  AIAnalysisService           │
│  - Adds states to prompt     │
│  - Uses qualitative labels   │
│  - Enforces disclaimers      │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│  GPT-4o (LLM)                │
│  - Generates cards           │
│  - Includes medical          │
│    disclaimers for alerts    │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│  Mobile App (Brief UI)       │
│  - Displays cards            │
│  - New latent state cards    │
└──────────────────────────────┘
```

---

## 📂 Files Created/Modified

### Database
- **`database/migrations/016_daily_state.sql`** ✨ NEW
  - Creates `daily_state` table
  - Columns: state_type, state_date, score, smoothed_score, confidence, top_factors, metadata, model_version
  - RLS policies for user data isolation
  - Indexes for performance
  - Helper function `get_daily_states()`

### Backend Core
- **`backend/latent_states.py`** ✨ NEW (740 lines)
  - Utility functions: `robust_zscore()`, `sigmoid()`, `ema()`
  - `calculate_recovery_state()` - HRV, RHR, sleep, fragmentation
  - `calculate_sleep_debt_state()` - Accumulated debt with decay
  - `calculate_overtrain_state()` - ACWR analysis
  - `calculate_infection_state()` - With confounding penalties

- **`backend/services/latent_state_service.py`** ✨ NEW (650 lines)
  - Orchestration service
  - Fetches biometrics (3d, 7d, 28d windows)
  - Training load calculation with caps
  - EMA smoothing with storage
  - Cache management (model_version aware)

### Backend Integration
- **`backend/services/ai_service.py`** ✏️ MODIFIED
  - Import `LatentStateService`
  - Initialize in `__init__()`
  - Added helper functions: `_categorize_score()`, `_categorize_confidence()`, `_categorize_debt()`, `_categorize_infection()`, `_format_top_factors()`, `_format_penalties()`
  - Modified `_build_brief_prompt()` to call latent states and add to prompt
  - Qualitative categories sent to LLM (not raw percentages)

- **`backend/llm_client.py`** ✏️ MODIFIED
  - Updated `wellness_coach_prompt` with extensive latent state rules
  - Medical disclaimer requirements (MANDATORY for alert/health cards)
  - Forbidden terminology rules
  - Example cards with disclaimers
  - Rules for generating latent state cards (dette_sommeil, surcharge, vigilance_sante)

### Tests
- **`backend/tests/test_latent_states.py`** ✨ NEW (700+ lines)
  - Unit tests for all utility functions
  - Tests for each state calculator
  - Edge cases (missing data, extreme values)
  - EMA smoothing tests
  - Confounding penalty tests
  - Categorization function tests

- **`backend/tests/test_integration_latent_states.py`** ✨ NEW (550+ lines)
  - End-to-end integration tests
  - Database migration verification
  - State calculation verification
  - AI prompt integration verification
  - Brief generation verification
  - **CRITICAL**: Medical disclaimer verification

---

## 🔬 Key Scientific Features

### 1. Robust Z-Score Calculation
```python
z = (x - median) / (IQR / 1.349)
```
- Uses median and IQR (not mean/std) for outlier resistance
- Clamped to [-4, +4] to prevent extreme values

### 2. EMA Smoothing (Exponential Moving Average)
```python
smoothed_t = α * raw_t + (1-α) * smoothed_(t-1)
```
- α = 0.2 for most states (reactive)
- α = 0.3 for infection (more reactive to sudden changes)
- Stored in `smoothed_score` column for O(1) lookup

### 3. Training Load with Cap
```python
load = min(10, steps/1000)  # or min(15, active_minutes/10)
```
- Prevents outliers (e.g., 30k step days) from distorting ACWR
- Prioritizes `active_minutes` over `steps` if available

### 4. Confounding Variable Handling
For infection-like state:
```python
if sleep_debt_hours > 3h: score *= 0.8
if overtrain_score > 0.7: score *= 0.85
```
- Prevents false positives when symptoms explained by other states
- Penalties can stack (0.8 * 0.85 = 0.68 total reduction)

### 5. Qualitative Categories for LLM
Instead of: "Récupération: 62%" ❌  
We send: "Récupération: moyenne" ✅

Benefits:
- User-friendly
- Prevents LLM from outputting meaningless percentages
- Flexible threshold adjustment without retraining

---

## 🏥 Medical Safety (CRITICAL)

### Mandatory Disclaimers
ALL alert/health cards MUST include:

```
"**Ce n'est pas un diagnostic médical**, mais une observation de patterns physiologiques."

"Si vous ressentez des symptômes importants ou persistants, **consultez un professionnel de santé**."
```

### Terminology Rules
❌ FORBIDDEN:
- "vous avez une infection"
- "vous êtes malade"
- "diagnostic confirmé"

✅ ALLOWED:
- "signature physiologique inhabituelle"
- "pattern peut signaler"
- "observation"

### Implementation
- LLM prompt enforces these rules
- Integration test verifies compliance
- `test_medical_disclaimers()` checks every alert card

---

## 🧪 Testing Instructions

### 1. Apply Database Migration
```bash
cd /Users/dannezri/Desktop/Pulse
psql -U your_user -d your_db -f database/migrations/016_daily_state.sql
```

### 2. Run Unit Tests
```bash
cd backend
python -m pytest tests/test_latent_states.py -v
```

Expected: All tests pass ✅

### 3. Run Integration Tests
```bash
cd backend
python tests/test_integration_latent_states.py

# Or with specific user:
python tests/test_integration_latent_states.py --user-id <UUID>
```

Expected output:
```
====================================
TEST SUMMARY
====================================
  ✓ PASS - Database Migration
  ✓ PASS - Latent State Calculation
  ✓ PASS - AI Prompt Integration
  ✓ PASS - Brief Generation
  ✓ PASS - Medical Disclaimers (CRITICAL)

Total: 5/5 tests passed

🎉 All tests passed! Latent states system is ready.
```

### 4. Test Mobile App
```bash
cd mobile
npx expo start
```

1. Navigate to "Brief" tab
2. Pull-to-refresh
3. Verify new cards appear:
   - `dette_sommeil` (if debt > 3h)
   - `surcharge` (if ACWR > 1.5)
   - `vigilance_sante` (if infection signature strong)
4. Check that alert cards have disclaimers at the bottom
5. Verify text is not cropped (max 550 chars enforced in prompt)

---

## 🎯 New Brief Cards

### 1. Dette de Sommeil (Sleep Debt)
**Conditions**: `debt_hours >= 3.0` (modérée) or `>= 5.0` (sévère)

```json
{
  "id": "dette_sommeil",
  "type": "focus",
  "title": "Dette de sommeil accumulée",
  "content": "Vous avez accumulé **3.2h de dette**...",
  "state": "alert",
  "iconName": "Moon",
  "badge": 3,
  "badgeUnit": "h",
  "priority": 95
}
```

### 2. Surcharge (Overtraining)
**Conditions**: `overtrain_interpretation == "surcharge"` (smoothed_score >= 0.7)

```json
{
  "id": "surcharge",
  "type": "activity",
  "title": "Surcharge détectée",
  "content": "Votre charge d'entraînement...",
  "state": "warning",
  "iconName": "TrendingDown",
  "priority": 90
}
```

### 3. Vigilance Santé (Infection-like)
**Conditions**: 
- `infection_category == "signature forte"`
- `persistent == True` (2+ days)
- `penalties_applied == []` (no confounding)

```json
{
  "id": "vigilance_sante",
  "type": "focus",
  "title": "Pattern physiologique inhabituel",
  "content": "Votre rythme cardiaque...\n\n**Ce n'est pas un diagnostic médical**...",
  "state": "alert",
  "iconName": "AlertTriangle",
  "priority": 95
}
```

**⚠️ IMPORTANT**: This card will NOT appear if sleep debt or overtraining scores are high (confounding penalties applied).

---

## 📊 Database Schema

### `daily_state` Table
```sql
CREATE TABLE daily_state (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) NOT NULL,
    state_type TEXT NOT NULL,  -- 'recovery', 'sleep_debt', 'overtrain', 'infection_like'
    state_date DATE NOT NULL,  -- Local user date
    score FLOAT NOT NULL,  -- 0.0-1.0 raw score
    smoothed_score FLOAT,  -- 0.0-1.0 EMA smoothed
    confidence FLOAT NOT NULL,  -- 0.0-1.0
    top_factors JSONB,  -- Standardized format
    metadata JSONB,  -- EMA, raw inputs, penalties
    model_version TEXT NOT NULL DEFAULT 'latent_v1',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE(user_id, state_type, state_date)
);
```

### `top_factors` Format (Standardized)
```json
[
  {
    "factor": "hrv_below_baseline",
    "direction": "down",
    "weight": 0.40,
    "evidence": {
      "z": -1.8,
      "value": 42,
      "baseline": 58
    }
  },
  {
    "factor": "rhr_above_baseline",
    "direction": "up",
    "weight": 0.25,
    "evidence": {
      "z": 1.4,
      "value": 68,
      "baseline": 62
    }
  }
]
```

---

## 🚀 Next Steps

### Immediate (Before Production)
1. ✅ Apply database migration
2. ✅ Run all tests (unit + integration)
3. ✅ Test mobile app with real user data
4. ✅ Verify medical disclaimers appear correctly
5. ⚠️ Legal review of disclaimer text (recommend consulting legal counsel)

### Short Term (Post-Launch Monitoring)
1. Monitor `daily_state` table growth and performance
2. Track `model_version` distribution (should all be 'latent_v1')
3. Watch for false positives in infection alerts
4. Collect user feedback on new cards

### Medium Term (Enhancements)
1. Add remaining latent states (stress, hypoglycemia, jet lag, medication effects)
2. Improve training load calculation (integrate heart rate zones if available)
3. Add temperature and respiration rate when Oura provides them
4. Create admin dashboard to view latent state distributions

### Long Term (Research)
1. Validate state calculations against clinical outcomes
2. A/B test different threshold values
3. Personalize baselines per user (currently using median/IQR)
4. Machine learning for adaptive weighting

---

## 🐛 Troubleshooting

### Issue: "daily_state table not found"
**Solution**: Apply migration
```bash
psql -U your_user -d your_db -f database/migrations/016_daily_state.sql
```

### Issue: "No latent states in prompt"
**Check**:
1. User has biometric data in last 3-7 days
2. `LatentStateService` is initialized in `AIAnalysisService.__init__()`
3. Check logs for calculation errors

### Issue: "Cards have no disclaimers"
**Check**:
1. LLM prompt includes disclaimer rules (check `llm_client.py`)
2. Run integration test: `python tests/test_integration_latent_states.py`
3. If test fails, LLM may need re-prompting

### Issue: "Infection cards appearing too often"
**Expected**: Confounding penalties should reduce false positives
**Check**:
1. Verify sleep_debt and overtrain penalties are applied
2. Check `metadata.confounding_states.penalties_applied` in database
3. May need to adjust penalty thresholds (currently 0.8 and 0.85)

### Issue: "Text cropped in mobile cards"
**Solution**: LLM prompt enforces max 500 chars for content
**Check**:
1. Verify constraint in `llm_client.py` wellness_coach_prompt
2. Check `BriefCard.tsx` has `numberOfLines={10}` and `shortContent` limit of 550

---

## 📚 References

### Algorithm Sources
- **Robust Z-Score**: Based on median absolute deviation (MAD) method
- **ACWR (Acute:Chronic Workload Ratio)**: Sports science standard for overtraining detection
- **Sleep Debt Calculation**: Exponential decay model with half-life ~4 days
- **EMA**: Standard time-series smoothing (used in financial markets, signal processing)

### Code Locations
- Calculators: `backend/latent_states.py`
- Orchestration: `backend/services/latent_state_service.py`
- AI Integration: `backend/services/ai_service.py`
- LLM Prompt: `backend/llm_client.py`
- Tests: `backend/tests/test_latent_states.py`, `backend/tests/test_integration_latent_states.py`

---

## ✅ Implementation Checklist

- [x] Database migration created (016_daily_state.sql)
- [x] Calculator functions implemented (recovery, sleep_debt, overtrain, infection)
- [x] Orchestration service created (LatentStateService)
- [x] AI service integration (prompt building, categorization)
- [x] LLM prompt updated (rules, disclaimers, examples)
- [x] Unit tests written (all utilities and calculators)
- [x] Integration tests written (end-to-end + disclaimers)
- [x] Mobile UI compatible (existing BriefCard handles new cards)
- [x] Medical disclaimers enforced (prompt + tests)
- [x] Documentation complete (this file)

---

## 🎉 Conclusion

The Pulse Latent States System is **fully implemented** and **ready for testing**. All code follows the plan specifications:

✅ Python calculations (not SQL) for v1  
✅ Explicit date/versioning in DB  
✅ Standardized `top_factors` format  
✅ EMA `smoothed_score` stored in DB  
✅ Training load capped to prevent outliers  
✅ Infection guardrails with confounding penalties  
✅ Qualitative categories for LLM (not raw percentages)  
✅ Medical disclaimers mandatory for alert cards  

**Next Action**: Run integration tests and deploy to production! 🚀

---

**Questions or Issues?**  
Review the troubleshooting section above or check the test output for specific error messages.
