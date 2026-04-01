#!/bin/bash
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LITELLM_URL="http://localhost:8001"
LITELLM_API_KEY="sk-test-1234567890"
POSTGRES_CONTAINER="litellm-db"
POSTGRES_USER="llmproxy"
POSTGRES_DB="litellm"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_COST=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bedrock Model Testing Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print section headers
print_header() {
    echo ""
    echo -e "${BLUE}[TEST]${NC} $1"
    echo "----------------------------------------"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to test LiteLLM health
test_health() {
    print_header "Testing LiteLLM Health"

    local response=$(curl -s -o /dev/null -w "%{http_code}" "${LITELLM_URL}/health/liveliness" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "LiteLLM health check: Connection failed (curl exit code: $curl_exit)"
        print_error "Is LiteLLM running on ${LITELLM_URL}?"
        return 1
    fi

    if [ "$response" -eq 200 ]; then
        print_success "LiteLLM health check: OK (HTTP $response)"
        return 0
    else
        print_error "LiteLLM health check: FAILED (HTTP $response)"
        return 1
    fi
}

# Function to list available models
test_models_list() {
    print_header "Listing Available Models"

    local response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${LITELLM_API_KEY}" \
        "${LITELLM_URL}/v1/models" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "Models endpoint: Connection failed (curl exit code: $curl_exit)"
        return 1
    fi

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        print_success "Models endpoint: OK (HTTP $http_code)"
        echo ""
        echo "Available models:"
        if echo "$body" | jq -e '.data' >/dev/null 2>&1; then
            echo "$body" | jq -r '.data[].id' 2>/dev/null | sed 's/^/  - /' || echo "  (error parsing model list)"
        else
            echo "  (no models found or invalid response)"
        fi
        return 0
    else
        print_error "Models endpoint: FAILED (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Function to test a specific model
test_model() {
    local model_name="$1"
    local test_prompt="$2"

    print_header "Testing Model: $model_name"

    # Prepare the request body
    local request_body=$(cat <<EOF
{
  "model": "$model_name",
  "messages": [
    {
      "role": "user",
      "content": "$test_prompt"
    }
  ],
  "max_tokens": 50
}
EOF
)

    # Make the API call
    local response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${LITELLM_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "${LITELLM_URL}/v1/chat/completions" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "Connection failed (curl exit code: $curl_exit)"
        return 1
    fi

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    # Check HTTP status code
    if [ "$http_code" -eq 200 ]; then
        print_success "HTTP Status: 200 OK"

        # Validate response structure
        local has_model=$(echo "$body" | jq -r '.model // empty' 2>/dev/null)
        local has_choices=$(echo "$body" | jq -r '.choices // empty' 2>/dev/null)
        local has_usage=$(echo "$body" | jq -r '.usage // empty' 2>/dev/null)

        if [ -n "$has_model" ] && [ -n "$has_choices" ] && [ -n "$has_usage" ]; then
            print_success "Response structure: Valid"

            # Extract and display key information
            local response_text=$(echo "$body" | jq -r '.choices[0].message.content' 2>/dev/null)
            local input_tokens=$(echo "$body" | jq -r '.usage.prompt_tokens' 2>/dev/null)
            local output_tokens=$(echo "$body" | jq -r '.usage.completion_tokens' 2>/dev/null)
            local total_tokens=$(echo "$body" | jq -r '.usage.total_tokens' 2>/dev/null)

            echo ""
            echo -e "${BLUE}Response:${NC} ${response_text:0:100}..."
            echo -e "${BLUE}Tokens:${NC} Input=$input_tokens, Output=$output_tokens, Total=$total_tokens"

            print_success "Model $model_name: PASSED"
            return 0
        else
            print_error "Response structure: Invalid (missing required fields)"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
            return 1
        fi
    elif [ "$http_code" -eq 401 ]; then
        print_error "HTTP Status: 401 Unauthorized (check LITELLM_API_KEY)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    elif [ "$http_code" -eq 403 ]; then
        print_error "HTTP Status: 403 Forbidden (check Bedrock IAM permissions)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    elif [ "$http_code" -eq 429 ]; then
        print_error "HTTP Status: 429 Too Many Requests (Bedrock throttling)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    else
        print_error "HTTP Status: $http_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Function to test embedding model
test_embedding() {
    local model_name="$1"
    local test_input="$2"

    print_header "Testing Embedding Model: $model_name"

    # Prepare the request body
    local request_body=$(cat <<EOF
{
  "model": "$model_name",
  "input": "$test_input"
}
EOF
)

    # Make the API call
    local response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${LITELLM_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "${LITELLM_URL}/v1/embeddings" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "Connection failed (curl exit code: $curl_exit)"
        return 1
    fi

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    # Check HTTP status code
    if [ "$http_code" -eq 200 ]; then
        print_success "HTTP Status: 200 OK"

        # Validate response structure
        local has_data=$(echo "$body" | jq -r '.data // empty' 2>/dev/null)
        local has_usage=$(echo "$body" | jq -r '.usage // empty' 2>/dev/null)

        if [ -n "$has_data" ] && [ -n "$has_usage" ]; then
            print_success "Response structure: Valid"

            # Extract and display key information
            local embedding_length=$(echo "$body" | jq -r '.data[0].embedding | length' 2>/dev/null)
            local total_tokens=$(echo "$body" | jq -r '.usage.total_tokens' 2>/dev/null)

            echo ""
            echo -e "${BLUE}Embedding dimensions:${NC} $embedding_length"
            echo -e "${BLUE}Tokens:${NC} $total_tokens"

            print_success "Model $model_name: PASSED"
            return 0
        else
            print_error "Response structure: Invalid (missing required fields)"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
            return 1
        fi
    else
        print_error "HTTP Status: $http_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Function to test rerank model
test_rerank() {
    local model_name="$1"

    print_header "Testing Rerank Model: $model_name"

    # Prepare the request body
    local request_body=$(cat <<EOF
{
  "model": "$model_name",
  "query": "What is the capital of France?",
  "documents": [
    "Paris is the capital of France and its largest city.",
    "London is the capital of England and the United Kingdom.",
    "Berlin is the capital and largest city of Germany."
  ],
  "top_n": 3
}
EOF
)

    # Make the API call
    local response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${LITELLM_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "${LITELLM_URL}/v1/rerank" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "Connection failed (curl exit code: $curl_exit)"
        return 1
    fi

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    # Check HTTP status code
    if [ "$http_code" -eq 200 ]; then
        print_success "HTTP Status: 200 OK"

        # Validate response structure
        local has_results=$(echo "$body" | jq -r '.results // empty' 2>/dev/null)

        if [ -n "$has_results" ]; then
            print_success "Response structure: Valid"

            # Extract and display key information
            local num_results=$(echo "$body" | jq -r '.results | length' 2>/dev/null)
            local top_index=$(echo "$body" | jq -r '.results[0].index' 2>/dev/null)
            local top_score=$(echo "$body" | jq -r '.results[0].relevance_score' 2>/dev/null)

            echo ""
            echo -e "${BLUE}Results returned:${NC} $num_results"
            echo -e "${BLUE}Top result:${NC} Document $top_index (score: $top_score)"

            print_success "Model $model_name: PASSED"
            return 0
        else
            print_error "Response structure: Invalid (missing results field)"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
            return 1
        fi
    else
        print_error "HTTP Status: $http_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Function to test image generation
test_image_generation() {
    local model_name="$1"
    local test_prompt="$2"

    print_header "Testing Image Generation: $model_name"

    # Prepare the request body
    local request_body=$(cat <<EOF
{
  "model": "$model_name",
  "prompt": "$test_prompt",
  "n": 1,
  "size": "512x512"
}
EOF
)

    # Make the API call
    local response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${LITELLM_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "${LITELLM_URL}/v1/images/generations" 2>/dev/null)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        print_error "Connection failed (curl exit code: $curl_exit)"
        return 1
    fi

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    # Check HTTP status code
    if [ "$http_code" -eq 200 ]; then
        print_success "HTTP Status: 200 OK"

        # Validate response structure
        local has_data=$(echo "$body" | jq -r '.data // empty' 2>/dev/null)

        if [ -n "$has_data" ]; then
            print_success "Response structure: Valid"

            # Extract and display key information
            local num_images=$(echo "$body" | jq -r '.data | length' 2>/dev/null)
            local image_format=$(echo "$body" | jq -r '.data[0].b64_json // "url"' 2>/dev/null)

            echo ""
            echo -e "${BLUE}Images generated:${NC} $num_images"
            if [ "$image_format" = "url" ]; then
                local image_url=$(echo "$body" | jq -r '.data[0].url' 2>/dev/null)
                echo -e "${BLUE}Image URL:${NC} ${image_url:0:50}..."
            else
                echo -e "${BLUE}Image format:${NC} base64 encoded"
            fi

            print_success "Model $model_name: PASSED"
            return 0
        else
            print_error "Response structure: Invalid (missing data field)"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
            return 1
        fi
    else
        print_error "HTTP Status: $http_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Function to check PostgreSQL cost logs
check_cost_logs() {
    print_header "Verifying PostgreSQL Cost Tracking"

    # Check if PostgreSQL container is running
    if ! podman ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER}$"; then
        print_error "PostgreSQL container not running: $POSTGRES_CONTAINER"
        return 1
    fi

    # Query recent spend logs
    local query="SELECT model, \"startTime\", \"endTime\", \"totalCost\", \"promptTokens\", \"completionTokens\" FROM \"LiteLLM_SpendLogs\" ORDER BY \"startTime\" DESC LIMIT 10;"

    echo ""
    echo "Recent cost tracking logs:"
    echo ""

    podman exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$query" 2>/dev/null || {
        print_error "Failed to query PostgreSQL cost logs"
        return 1
    }

    # Get total cost from recent tests
    local total_query="SELECT COALESCE(SUM(\"totalCost\"), 0) as total FROM \"LiteLLM_SpendLogs\" WHERE \"startTime\" > NOW() - INTERVAL '1 hour';"
    local total_cost=$(podman exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "$total_query" 2>/dev/null | tr -d ' ')

    if [ -n "$total_cost" ]; then
        echo ""
        print_success "PostgreSQL cost tracking: Operational"
        echo -e "${BLUE}Total cost (last hour):${NC} \$$total_cost"
    else
        print_warning "Unable to calculate total cost"
    fi
}

# Function to print test summary
print_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Tests Passed:  ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed:  ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        return 1
    fi
}

# Main test execution
main() {
    echo "Starting Bedrock model tests..."
    echo ""

    # Test 1: LiteLLM Health (CRITICAL - abort if failed)
    if ! test_health; then
        echo ""
        echo -e "${RED}CRITICAL: LiteLLM is not responding. Cannot continue tests.${NC}"
        echo -e "${YELLOW}Please ensure LiteLLM is running: ./manage.sh status${NC}"
        return 1
    fi

    # Test 2: List Models (informational - continue even if failed)
    test_models_list || echo -e "${YELLOW}Warning: Could not list models, but continuing tests...${NC}"

    # === Text Models (Claude) ===

    # Test 3: Claude Haiku 4.5 (baseline - should already be approved)
    test_model "claude-haiku-4-5" "Say hello" || true

    # Test 4: Claude Sonnet 4.6 (may require approval)
    test_model "claude-sonnet-4-6" "Name one color" || true

    # Test 5: Claude Opus 4.6 (may require approval)
    test_model "claude-opus-4-6" "What is 2+2?" || true

    # === Text Models (Other) ===

    # Test 6: Kimi K2.5 (multimodal with agent swarm)
    test_model "kimi-k2-5" "What is the weather like?" || true

    # === Image Generation ===

    # Test 7: Amazon Titan Image Generator V2
    test_image_generation "titan-image-v2" "A red ball on a green field" || true

    # === Embeddings ===

    # Test 8: Amazon Titan Embed Text V2
    test_embedding "titan-embed-v2" "The quick brown fox jumps over the lazy dog" || true

    # === Rerank ===

    # Test 9: Cohere Rerank V3.5
    test_rerank "cohere-rerank-v3-5" || true

    # === Cost Tracking ===

    # Test 10: PostgreSQL Cost Tracking (informational - continue even if failed)
    check_cost_logs || echo -e "${YELLOW}Warning: Cost tracking check failed${NC}"

    # Print summary
    print_summary
}

# Run main function
main
