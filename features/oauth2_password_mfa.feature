Feature: OAuth2 password grant with MFA support

  Scenario: Password grant without MFA works normally
    Given a verified user and an OAuth2 client with all grants
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "token-bdd@example.com", "password": "securepassword123", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value", "scope": "openid profile"}
      """
    Then the response status code should be 200
    And the response should have JSON key "access_token"

  Scenario: Password grant with MFA enabled returns mfa_required
    Given a user with MFA enabled and an OAuth2 client
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "${mfa_user_email}", "password": "securepassword123", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value", "scope": "openid"}
      """
    Then the response status code should be 403
    And the response body should contain "mfa_required"
    And the response should have JSON key "mfa_token"

  Scenario: Password grant MFA completion with TOTP code returns tokens
    Given a user with MFA enabled and an OAuth2 client
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "username": "${mfa_user_email}", "password": "securepassword123", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value", "scope": "openid"}
      """
    Then the response status code should be 403
    When I send a form POST to "/oauth2/token" with
      """
      {"grant_type": "password", "mfa_token": "${mfa_login_token}", "mfa_code": "${mfa_totp_code}", "client_id": "bdd-full-client", "client_secret": "bdd-test-secret-value", "scope": "openid"}
      """
    Then the response status code should be 200
    And the response should have JSON key "access_token"
    And the response should have JSON key "refresh_token"
