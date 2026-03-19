Feature: User login

  Scenario: Successful login returns 200 with user_id
    Given a registered and verified user "login-happy@example.com" with password "securepassword123"
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "login-happy@example.com", "password": "securepassword123"}
      """
    Then the response status code should be 200
    And the response body should contain "user_id"

  Scenario: Login with invalid credentials returns 401
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "nobody@example.com", "password": "wrongpassword"}
      """
    Then the response status code should be 401
    And the response body should contain "Invalid email or password"

  Scenario: Login with missing password returns 422
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "test@example.com", "password": ""}
      """
    Then the response status code should be 422
