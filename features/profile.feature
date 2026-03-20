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

  # --- Profile update ---

  Scenario: PUT /api/me/profile without auth returns 401
    When I send a PUT request to "/api/me/profile"
    Then the response status code should be 401

  Scenario: PUT /api/me/profile with Bearer updates profile
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a PUT request to "/api/me/profile" with JSON
      """
      {"name": "Updated Name", "locale": "fr-FR"}
      """
    Then the response status code should be 200
    And the response body should contain "Profile updated"

  # --- Email management ---

  Scenario: POST /api/me/emails without auth returns 401
    When I send a POST request to "/api/me/emails"
    Then the response status code should be 401

  Scenario: DELETE /api/me/emails without auth returns 401
    When I send a DELETE request to "/api/me/emails/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 401
