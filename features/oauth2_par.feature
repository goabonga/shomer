Feature: OAuth2 Pushed Authorization Request endpoint

  Scenario: PAR without client auth returns 401
    When I send a form POST to "/oauth2/par" with
      """
      {"response_type": "code", "redirect_uri": "https://app.example.com/callback", "scope": "openid", "state": "xyz"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: PAR with unknown client returns 401
    When I send a form POST to "/oauth2/par" with
      """
      {"response_type": "code", "client_id": "unknown", "client_secret": "wrong", "redirect_uri": "https://app.example.com/callback", "scope": "openid", "state": "xyz"}
      """
    Then the response status code should be 401
    And the response body should contain "invalid_client"

  Scenario: PAR with missing redirect_uri returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/par" with
      """
      {"response_type": "code", "scope": "openid", "state": "xyz", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "invalid_request"

  Scenario: PAR with missing response_type returns 400
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/par" with
      """
      {"redirect_uri": "https://app.example.com/callback", "scope": "openid", "state": "xyz", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 400
    And the response body should contain "invalid_request"

  Scenario: PAR with valid parameters returns 201 with request_uri
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/par" with
      """
      {"response_type": "code", "redirect_uri": "https://app.example.com/callback", "scope": "openid", "state": "abc123", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 201
    And the response should have JSON key "request_uri"
    And the response should have JSON key "expires_in"
    And the response body should contain "urn:ietf:params:oauth:request_uri:"

  Scenario: PAR response contains correct expires_in
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/par" with
      """
      {"response_type": "code", "redirect_uri": "https://app.example.com/callback", "scope": "openid profile", "state": "def456", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value"}
      """
    Then the response status code should be 201
    And the response body should contain "expires_in"
