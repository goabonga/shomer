Feature: Personal Access Token API

  Scenario: POST /api/pats without auth returns 401
    When I send a POST request to "/api/pats" with JSON
      """
      {"name": "test-key", "scopes": "api:read"}
      """
    Then the response status code should be 401

  Scenario: GET /api/pats without auth returns 401
    When I send a GET request to "/api/pats"
    Then the response status code should be 401

  Scenario: DELETE /api/pats/00000000-0000-0000-0000-000000000001 without auth returns 401
    When I send a DELETE request to "/api/pats/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: POST /api/pats with auth creates token and returns it
    Given a registered and verified user "pat-create@example.com" with password "securepassword123"
    And I am logged in as "pat-create@example.com" with password "securepassword123"
    When I send a POST request to "/api/pats" with JSON
      """
      {"name": "my-ci-key", "scopes": "api:read api:write"}
      """
    Then the response status code should be 201
    And the response should have JSON key "token"
    And the response should have JSON key "name"
    And the response body should contain "shm_pat_"
    And the response body should contain "my-ci-key"
    And the response body should contain "Save this token"

  Scenario: GET /api/pats with auth returns list of tokens
    Given a registered and verified user "pat-list@example.com" with password "securepassword123"
    And I am logged in as "pat-list@example.com" with password "securepassword123"
    When I send a POST request to "/api/pats" with JSON
      """
      {"name": "list-key", "scopes": "api:read"}
      """
    Then the response status code should be 201
    When I send a GET request to "/api/pats"
    Then the response status code should be 200
    And the response should have JSON key "tokens"
    And the response body should contain "list-key"
    And the response body should contain "shm_pat_"

  Scenario: DELETE /api/pats/{id} with auth revokes token
    Given a registered and verified user "pat-revoke@example.com" with password "securepassword123"
    And I am logged in as "pat-revoke@example.com" with password "securepassword123"
    When I send a POST request to "/api/pats" with JSON
      """
      {"name": "revoke-key", "scopes": ""}
      """
    Then the response status code should be 201
    When I send a GET request to "/api/pats"
    Then the response status code should be 200
    And the response body should contain "revoke-key"
