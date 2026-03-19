Feature: OAuth2 authorization endpoint

  Scenario: Valid authorize request shows login page for unauthenticated user
    Given an authenticated user with an OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid&state=abc123"
    Then the response status code should be 200
    And the response body should contain "Login"

  Scenario: Missing client_id without redirect_uri returns 400
    When I send a GET request to "/oauth2/authorize?response_type=code"
    Then the response status code should be 400
    And the response body should contain "client_id"

  Scenario: Missing state without redirect_uri returns 400
    When I send a GET request to "/oauth2/authorize?client_id=unknown&response_type=code"
    Then the response status code should be 400

  # --- PKCE enforcement ---

  Scenario: Public client without code_challenge returns 400
    Given a public OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-public-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid&state=pkce1"
    Then the response status code should be 400
    And the response body should contain "code_challenge is required"

  Scenario: Public client with code_challenge succeeds
    Given a public OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-public-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid&state=pkce2&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256"
    Then the response status code should be 200
    And the response body should contain "Login"

  Scenario: Confidential client without code_challenge succeeds
    Given an authenticated user with an OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid&state=pkce3"
    Then the response status code should be 200
    And the response body should contain "Login"
