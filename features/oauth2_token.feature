Feature: OAuth2 token endpoint

  Scenario: Token endpoint without grant_type returns 422
    When I send a POST request to "/oauth2/token"
    Then the response status code should be 422

  Scenario: Unsupported grant_type returns 400
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "implicit"}
      """
    Then the response status code should be 400
    And the response body should contain "unsupported_grant_type"

  Scenario: Missing client credentials returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "authorization_code", "code": "fake", "redirect_uri": "https://app.example.com/cb"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Unknown client_id returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "authorization_code", "code": "fake", "redirect_uri": "https://app.example.com/cb", "client_id": "unknown-client", "client_secret": "wrong"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Token response includes error format per RFC 6749
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "authorization_code", "code": "fake", "redirect_uri": "https://app.example.com/cb", "client_id": "x", "client_secret": "y"}
      """
    Then the response status code should be 401
    And the response should have JSON key "error"
    And the response should have JSON key "error_description"
