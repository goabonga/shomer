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
