Feature: User registration

  Scenario: Successful registration
    When I send a POST request to "/auth/register" with JSON
      """
      {"email": "newuser@example.com", "password": "securepassword123"}
      """
    Then the response status code should be 201
    And the response body should contain "user_id"
    And the response body should contain "Registration successful"

  Scenario: Registration with username
    When I send a POST request to "/auth/register" with JSON
      """
      {"email": "withname@example.com", "password": "securepassword123", "username": "johndoe"}
      """
    Then the response status code should be 201
    And the response body should contain "user_id"

  Scenario: Duplicate email still returns 201 (anti-enumeration)
    Given I have a JSON payload
      """
      {"email": "duplicate@example.com", "password": "securepassword123"}
      """
    When I send a POST request to "/auth/register"
    Then the response status code should be 201
    Given I have a JSON payload
      """
      {"email": "duplicate@example.com", "password": "anotherpassword1"}
      """
    When I send a POST request to "/auth/register"
    Then the response status code should be 201
    And the response body should contain "Registration successful"

  Scenario: Weak password returns 422
    When I send a POST request to "/auth/register" with JSON
      """
      {"email": "weak@example.com", "password": "short"}
      """
    Then the response status code should be 422

  Scenario: Invalid email returns 422
    When I send a POST request to "/auth/register" with JSON
      """
      {"email": "not-an-email", "password": "securepassword123"}
      """
    Then the response status code should be 422
