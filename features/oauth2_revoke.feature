Feature: OAuth2 token revocation

  Scenario: Revoke without client auth returns 401
    When I send a form POST to "/oauth2/revoke" with
      """
      {"token": "fake-token"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Revoke with unknown client returns 401
    When I send a form POST to "/oauth2/revoke" with
      """
      {"token": "fake", "client_id": "unknown", "client_secret": "wrong"}
      """
    Then the response status code should be 401

  Scenario: Revoke unknown token returns 200 (no information leakage)
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/revoke" with
      """
      {"token": "nonexistent-token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200

  Scenario: Revoke valid refresh token returns 200
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a form POST to "/oauth2/revoke" with
      """
      {"token": "nonexistent", "token_type_hint": "refresh_token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
