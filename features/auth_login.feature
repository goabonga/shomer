Feature: User login

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
