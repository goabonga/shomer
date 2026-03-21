Feature: MFA setup and management API

  Scenario: GET /mfa/status without auth returns 401
    When I send a GET request to "/mfa/status"
    Then the response status code should be 401

  Scenario: POST /mfa/setup without auth returns 401
    When I send a POST request to "/mfa/setup"
    Then the response status code should be 401

  Scenario: POST /mfa/enable without auth returns 401
    When I send a POST request to "/mfa/enable" with JSON
      """
      {"code": "123456"}
      """
    Then the response status code should be 401

  Scenario: POST /mfa/disable without auth returns 401
    When I send a POST request to "/mfa/disable" with JSON
      """
      {"code": "123456"}
      """
    Then the response status code should be 401

  Scenario: POST /mfa/backup-codes without auth returns 401
    When I send a POST request to "/mfa/backup-codes" with JSON
      """
      {"code": "123456"}
      """
    Then the response status code should be 401

  Scenario: GET /mfa/status with auth returns status
    Given a registered and verified user "mfa-status@example.com" with password "securepassword123"
    And I am logged in as "mfa-status@example.com" with password "securepassword123"
    When I send a GET request to "/mfa/status"
    Then the response status code should be 200
    And the response should have JSON key "mfa_enabled"
    And the response body should contain "false"

  Scenario: POST /mfa/setup with auth returns provisioning URI
    Given a registered and verified user "mfa-setup@example.com" with password "securepassword123"
    And I am logged in as "mfa-setup@example.com" with password "securepassword123"
    When I send a POST request to "/mfa/setup"
    Then the response status code should be 200
    And the response should have JSON key "secret"
    And the response should have JSON key "provisioning_uri"
    And the response body should contain "otpauth://totp/"
