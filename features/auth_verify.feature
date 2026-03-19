Feature: Email verification

  Scenario: Successful verification returns 200
    Given I register and verify "verify-happy@example.com" with password "securepassword123"
    Then I should receive an email at "verify-happy@example.com"

  Scenario: Verify with invalid code returns 400
    When I send a POST request to "/auth/verify" with JSON
      """
      {"email": "nobody@example.com", "code": "000000"}
      """
    Then the response status code should be 400
    And the response body should contain "Invalid or expired"

  Scenario: Resend for unknown email returns 404
    When I send a POST request to "/auth/verify/resend" with JSON
      """
      {"email": "unknown@example.com"}
      """
    Then the response status code should be 404
    And the response body should contain "Email not found"

  Scenario: Resend for recently registered email returns 429 (rate limited)
    When I send a POST request to "/auth/register" with JSON
      """
      {"email": "resend-rate@example.com", "password": "securepassword123"}
      """
    Then the response status code should be 201
    When I send a POST request to "/auth/verify/resend" with JSON
      """
      {"email": "resend-rate@example.com"}
      """
    Then the response status code should be 429
    And the response body should contain "wait"

  Scenario: Verify with short code returns 422
    When I send a POST request to "/auth/verify" with JSON
      """
      {"email": "test@example.com", "code": "123"}
      """
    Then the response status code should be 422
