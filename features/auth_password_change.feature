Feature: Password change

  Scenario: Change password without session returns 401
    When I send a POST request to "/auth/password/change" with JSON
      """
      {"current_password": "old", "new_password": "newpassword1"}
      """
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: Change password with short new password returns 422
    When I send a POST request to "/auth/password/change" with JSON
      """
      {"current_password": "oldpassword", "new_password": "short"}
      """
    Then the response status code should be 422
