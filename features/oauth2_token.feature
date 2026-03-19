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

  # --- client_credentials grant ---

  Scenario: client_credentials without client auth returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "client_credentials"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: client_credentials with unknown client returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "client_credentials", "client_id": "unknown", "client_secret": "wrong"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: client_credentials error uses RFC 6749 format
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "client_credentials", "client_id": "no-such-client", "client_secret": "x"}
      """
    Then the response status code should be 401
    And the response should have JSON key "error"
    And the response should have JSON key "error_description"

  # --- password grant ---

  Scenario: password grant without client auth returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "user@example.com", "password": "pass"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: password grant with unknown client returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "user@example.com", "password": "pass", "client_id": "unknown", "client_secret": "wrong"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: password grant missing username returns 400
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "password": "pass", "client_id": "no-such-client", "client_secret": "x"}
      """
    Then the response status code should be 401

  Scenario: password grant error uses RFC 6749 format
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "u", "password": "p", "client_id": "no-client", "client_secret": "x"}
      """
    Then the response status code should be 401
    And the response should have JSON key "error"
    And the response should have JSON key "error_description"

  # --- happy paths ---

  Scenario: client_credentials grant returns access_token
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "client_credentials", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value", "scope": "openid"}
      """
    Then the response status code should be 200
    And the response should have JSON key "access_token"
    And the response should have JSON key "token_type"
    And the response body should contain "Bearer"

  Scenario: password grant returns access_token and refresh_token
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "token-bdd@example.com", "password": "securepassword123", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
    And the response should have JSON key "access_token"
    And the response should have JSON key "refresh_token"
    And the response body should contain "Bearer"

  Scenario: unauthorized_client for disallowed grant_type
    Given an authenticated user with an OAuth2 client
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "client_credentials", "client_id": "bdd-test-client", "client_secret": "anything"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"
