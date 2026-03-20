Feature: User profile endpoint

  Scenario: GET /api/me without auth returns 401
    When I send a GET request to "/api/me"
    Then the response status code should be 401

  Scenario: GET /api/me with Bearer token returns user profile
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a GET request to "/api/me"
    Then the response status code should be 200
    And the response should have JSON key "user_id"
    And the response should have JSON key "auth_method"
    And the response should have JSON key "emails"

  Scenario: GET /api/me with session cookie returns user profile
    Given a registered and verified user "me-session@example.com" with password "securepassword123"
    And I am logged in as "me-session@example.com" with password "securepassword123"
    When I send a GET request to "/api/me"
    Then the response status code should be 200
    And the response should have JSON key "user_id"
    And the response body should contain "me-session@example.com"
