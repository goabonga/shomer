Feature: Password reset

  Scenario: Request reset for known email returns 200 and sends email
    Given a registered and verified user "reset-happy@example.com" with password "securepassword123"
    When I send a POST request to "/auth/password/reset" with JSON
      """
      {"email": "reset-happy@example.com"}
      """
    Then the response status code should be 200
    And the response body should contain "reset link has been sent"
    And I should receive an email at "reset-happy@example.com"

  Scenario: Request reset for unknown email still returns 200
    When I send a POST request to "/auth/password/reset" with JSON
      """
      {"email": "nobody@example.com"}
      """
    Then the response status code should be 200
    And the response body should contain "reset link has been sent"

  Scenario: Reset verify with invalid token returns 400
    When I send a POST request to "/auth/password/reset-verify" with JSON
      """
      {"token": "00000000-0000-0000-0000-000000000000", "new_password": "newstrongpassword"}
      """
    Then the response status code should be 400
    And the response body should contain "Invalid or expired"

  Scenario: Reset verify with malformed token returns 400
    When I send a POST request to "/auth/password/reset-verify" with JSON
      """
      {"token": "not-a-uuid", "new_password": "newstrongpassword"}
      """
    Then the response status code should be 400

  Scenario: Reset verify with short password returns 422
    When I send a POST request to "/auth/password/reset-verify" with JSON
      """
      {"token": "00000000-0000-0000-0000-000000000000", "new_password": "short"}
      """
    Then the response status code should be 422
