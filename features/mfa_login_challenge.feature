Feature: Two-step MFA login challenge

  Scenario: Login without MFA returns normal session
    Given a registered and verified user "mfa-no-mfa@example.com" with password "securepassword123"
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "mfa-no-mfa@example.com", "password": "securepassword123"}
      """
    Then the response status code should be 200
    And the response body should contain "Login successful"

  Scenario: Login with MFA enabled returns mfa_required
    Given a user with MFA enabled
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "${mfa_user_email}", "password": "securepassword123"}
      """
    Then the response status code should be 200
    And the response should have JSON key "mfa_required"
    And the response should have JSON key "mfa_token"
    And the response body should contain "true"

  Scenario: Complete MFA challenge with TOTP code creates session
    Given a user with MFA enabled
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "${mfa_user_email}", "password": "securepassword123"}
      """
    Then the response status code should be 200
    And the response should have JSON key "mfa_token"
    When I send a POST request to "/mfa/verify-challenge" with JSON
      """
      {"mfa_token": "${mfa_login_token}", "code": "${mfa_totp_code}", "method": "totp"}
      """
    Then the response status code should be 200
    And the response body should contain "Login complete"

  Scenario: MFA challenge with invalid token returns 401
    When I send a POST request to "/mfa/verify-challenge" with JSON
      """
      {"mfa_token": "invalid-token", "code": "123456", "method": "totp"}
      """
    Then the response status code should be 401
    And the response body should contain "Invalid or expired MFA token"

  Scenario: MFA challenge with wrong TOTP code returns 400
    Given a user with MFA enabled
    When I send a POST request to "/auth/login" with JSON
      """
      {"email": "${mfa_user_email}", "password": "securepassword123"}
      """
    Then the response status code should be 200
    When I send a POST request to "/mfa/verify-challenge" with JSON
      """
      {"mfa_token": "${mfa_login_token}", "code": "000000", "method": "totp"}
      """
    Then the response status code should be 400
    And the response body should contain "Invalid TOTP"
