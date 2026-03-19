Feature: Password change

  Scenario: Successful password change returns 200
    Given a registered and verified user "change-happy@example.com" with password "securepassword123"
    And I am logged in as "change-happy@example.com" with password "securepassword123"
    When I send a POST request to "/auth/password/change" with JSON
      """
      {"current_password": "securepassword123", "new_password": "newsecurepassword1"}
      """
    Then the response status code should be 200
    And the response body should contain "Password changed successfully"

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
