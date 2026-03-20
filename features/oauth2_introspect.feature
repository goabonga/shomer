Feature: OAuth2 token introspection

  Scenario: Introspect without client auth returns 401
    When I send a form POST to "/oauth2/introspect" with
      """
      {"token": "fake-token"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Introspect with unknown client returns 401
    When I send a form POST to "/oauth2/introspect" with
      """
      {"token": "fake", "client_id": "unknown", "client_secret": "wrong"}
      """
    Then the response status code should be 401

  Scenario: Introspect unknown token returns active false
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/introspect" with
      """
      {"token": "nonexistent", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
    And the response body should contain "false"

  Scenario: Introspect valid access token returns active true
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a form POST to "/oauth2/introspect" with
      """
      {"token": "${bearer_token}", "token_type_hint": "access_token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
    And the response body should contain "true"
    And the response should have JSON key "scope"
    And the response should have JSON key "client_id"
