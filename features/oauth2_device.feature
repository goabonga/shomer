Feature: OAuth2 Device Authorization endpoint

  Scenario: Device auth without client auth returns 401
    When I send a form POST to "/oauth2/device" with
      """
      {"scope": "openid"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Device auth with unknown client returns 401
    When I send a form POST to "/oauth2/device" with
      """
      {"scope": "openid", "client_id": "unknown", "client_secret": "wrong"}
      """
    Then the response status code should be 401

  Scenario: Device auth with valid client returns device_code and user_code
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/device" with
      """
      {"scope": "openid", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
    And the response should have JSON key "device_code"
    And the response should have JSON key "user_code"
    And the response should have JSON key "verification_uri"
    And the response should have JSON key "expires_in"
    And the response should have JSON key "interval"

  Scenario: Device auth response includes verification_uri_complete
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/device" with
      """
      {"scope": "openid profile", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 200
    And the response should have JSON key "verification_uri_complete"
