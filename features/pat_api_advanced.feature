Feature: PAT API usage stats

  Scenario: GET /api/pats returns usage stats fields
    Given a registered and verified user "pat-api-stats@example.com" with password "securepassword123"
    And I am logged in as "pat-api-stats@example.com" with password "securepassword123"
    When I send a POST request to "/api/pats" with JSON
      """
      {"name": "stats-api-key", "scopes": "api:read"}
      """
    Then the response status code should be 201
    When I send a GET request to "/api/pats"
    Then the response status code should be 200
    And the response should have JSON key "tokens"
    And the response body should contain "use_count"
    And the response body should contain "last_used_ip"
    And the response body should contain "stats-api-key"
