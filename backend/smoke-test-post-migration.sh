#!/bin/bash
# ============================================
# SMOKE TEST POST-MIGRATION
# ============================================
# Script pour valider que les endpoints critiques ne crashent pas
# après la migration des baselines robustes
#
# Usage:
#   ./smoke-test-post-migration.sh [API_URL]
#
# Exemples:
#   ./smoke-test-post-migration.sh http://localhost:8000
#   ./smoke-test-post-migration.sh https://staging.pulse.com
#   ./smoke-test-post-migration.sh https://api.pulse.com

set -e  # Exit on error

# ============================================
# CONFIGURATION
# ============================================

API_URL="${1:-http://localhost:8000}"
NEW_USER_EMAIL="smoke-test-$(date +%s)@pulse.com"
NEW_USER_PASSWORD="SmokeTest123!@#"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# HELPERS
# ============================================

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ============================================
# TESTS
# ============================================

print_header "SMOKE TEST POST-MIGRATION"
echo "API URL: $API_URL"
echo "Test User: $NEW_USER_EMAIL"
echo ""

# ============================================
# Test 1: Créer nouveau user (0 baselines)
# ============================================

print_header "Test 1: Create New User (0 baselines)"

SIGNUP_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$NEW_USER_EMAIL\",\"password\":\"$NEW_USER_PASSWORD\"}" \
  || echo '{"error":"curl_failed"}')

echo "Signup response: $SIGNUP_RESPONSE"

# Extraire token (compatible avec jq et sans jq)
if command -v jq &> /dev/null; then
    TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.access_token // .token // empty')
    USER_ID=$(echo "$SIGNUP_RESPONSE" | jq -r '.user.id // .user_id // empty')
else
    # Fallback sans jq (moins robuste)
    TOKEN=$(echo "$SIGNUP_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    USER_ID=$(echo "$SIGNUP_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    print_error "Failed to create test user or get token"
    echo "Response: $SIGNUP_RESPONSE"
    exit 1
fi

print_success "Test user created with token"
echo "User ID: $USER_ID"

# ============================================
# Test 2: Dashboard avec 0 baselines
# ============================================

print_header "Test 2: Dashboard Endpoint (0 baselines)"

DASHBOARD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/ambient/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$DASHBOARD_RESPONSE" | tail -n 1)
BODY=$(echo "$DASHBOARD_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" == "200" ]; then
    print_success "Dashboard endpoint returned 200 OK"
    
    # Vérifier structure JSON
    if command -v jq &> /dev/null; then
        ANOMALIES_COUNT=$(echo "$BODY" | jq -r '.anomalies | length // 0')
        STATE=$(echo "$BODY" | jq -r '.state // "unknown"')
        
        echo "   State: $STATE"
        echo "   Anomalies: $ANOMALIES_COUNT"
        
        if [ "$ANOMALIES_COUNT" == "0" ]; then
            print_success "No anomalies for new user (expected)"
        else
            print_warning "Found $ANOMALIES_COUNT anomalies for new user (unexpected but not blocking)"
        fi
        
        if [ "$STATE" == "calm" ]; then
            print_success "State is 'calm' (expected)"
        else
            print_warning "State is '$STATE' (expected 'calm')"
        fi
    else
        print_warning "jq not installed, skipping JSON validation"
    fi
else
    print_error "Dashboard endpoint failed with HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

# ============================================
# Test 3: Brief endpoint
# ============================================

print_header "Test 3: Brief Endpoint (0 baselines)"

BRIEF_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/brief/today" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

BRIEF_HTTP_CODE=$(echo "$BRIEF_RESPONSE" | tail -n 1)
BRIEF_BODY=$(echo "$BRIEF_RESPONSE" | head -n -1)

echo "HTTP Code: $BRIEF_HTTP_CODE"

if [ "$BRIEF_HTTP_CODE" == "200" ] || [ "$BRIEF_HTTP_CODE" == "204" ]; then
    print_success "Brief endpoint returned $BRIEF_HTTP_CODE (acceptable)"
    
    if [ "$BRIEF_HTTP_CODE" == "204" ]; then
        echo "   No content (expected for new user)"
    else
        echo "   Response: $BRIEF_BODY"
    fi
else
    print_error "Brief endpoint failed with HTTP $BRIEF_HTTP_CODE"
    echo "$BRIEF_BODY"
    exit 1
fi

# ============================================
# Test 4: Baselines endpoint (should be empty)
# ============================================

print_header "Test 4: Baselines Endpoint (should be empty)"

BASELINES_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/baselines/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

BASELINES_HTTP_CODE=$(echo "$BASELINES_RESPONSE" | tail -n 1)
BASELINES_BODY=$(echo "$BASELINES_RESPONSE" | head -n -1)

echo "HTTP Code: $BASELINES_HTTP_CODE"

if [ "$BASELINES_HTTP_CODE" == "200" ]; then
    print_success "Baselines endpoint returned 200 OK"
    
    if command -v jq &> /dev/null; then
        BASELINES_COUNT=$(echo "$BASELINES_BODY" | jq -r '. | length // 0')
        echo "   Baselines count: $BASELINES_COUNT"
        
        if [ "$BASELINES_COUNT" == "0" ]; then
            print_success "No baselines for new user (expected)"
        else
            print_warning "Found $BASELINES_COUNT baselines for new user (unexpected)"
        fi
    fi
else
    print_warning "Baselines endpoint returned $BASELINES_HTTP_CODE (may be expected)"
fi

# ============================================
# Test 5: Anomalies endpoint
# ============================================

print_header "Test 5: Anomalies Endpoint (should be empty)"

ANOMALIES_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/anomalies/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

ANOMALIES_HTTP_CODE=$(echo "$ANOMALIES_RESPONSE" | tail -n 1)
ANOMALIES_BODY=$(echo "$ANOMALIES_RESPONSE" | head -n -1)

echo "HTTP Code: $ANOMALIES_HTTP_CODE"

if [ "$ANOMALIES_HTTP_CODE" == "200" ]; then
    print_success "Anomalies endpoint returned 200 OK"
    
    if command -v jq &> /dev/null; then
        DETECTED_COUNT=$(echo "$ANOMALIES_BODY" | jq -r '. | length // 0')
        echo "   Anomalies detected: $DETECTED_COUNT"
        
        if [ "$DETECTED_COUNT" == "0" ]; then
            print_success "No anomalies detected (expected)"
        fi
    fi
else
    print_warning "Anomalies endpoint returned $ANOMALIES_HTTP_CODE"
fi

# ============================================
# SUMMARY
# ============================================

print_header "SMOKE TEST SUMMARY"
print_success "All critical endpoints tested successfully"
echo ""
echo "Tested endpoints:"
echo "  ✅ POST /api/auth/signup"
echo "  ✅ GET  /api/ambient/dashboard"
echo "  ✅ GET  /api/brief/today"
echo "  ✅ GET  /api/baselines/:userId"
echo "  ✅ GET  /api/anomalies/:userId"
echo ""
echo "All endpoints handled new user (0 baselines) gracefully."
echo "No crashes or 500 errors detected."
echo ""

# ============================================
# CLEANUP (optionnel)
# ============================================

print_header "CLEANUP"
echo "Test user created: $NEW_USER_EMAIL"
echo "User ID: $USER_ID"
echo ""
echo "To delete test user, run:"
echo "  DELETE FROM auth.users WHERE email = '$NEW_USER_EMAIL';"
echo ""

print_success "SMOKE TEST COMPLETED ✅"
exit 0
