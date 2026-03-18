Feature: JWKS endpoint (RFC 7517)

  Scenario: JWKS returns valid JSON with keys array
    When I send a GET request to "/.well-known/jwks.json"
    Then the response status code should be 200
    And the response should have JSON key "keys"

  Scenario: JWKS returns Cache-Control header
    When I send a GET request to "/.well-known/jwks.json"
    Then the response status code should be 200
    And the response should have header "Cache-Control" containing "max-age"

  Scenario: JWKS content type is JSON
    When I send a GET request to "/.well-known/jwks.json"
    Then the response status code should be 200
    And the response content type should be json
