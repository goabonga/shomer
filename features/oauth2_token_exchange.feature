Feature: OAuth2 Token Exchange grant (RFC 8693)

  Scenario: Token exchange without client auth returns 401
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": "tok", "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: Token exchange with missing subject_token returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token_type": "urn:ietf:params:oauth:token-type:access_token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "subject_token is required"

  Scenario: Token exchange with missing subject_token_type returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": "some-token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "subject_token_type is required"

  Scenario: Token exchange with invalid subject_token_type returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": "some-token", "subject_token_type": "bad:type", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "Unsupported token type"

  Scenario: Token exchange with unauthorized client returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": "some-token", "subject_token_type": "urn:ietf:params:oauth:token-type:access_token", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "unauthorized_client"
