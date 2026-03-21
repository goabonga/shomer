Feature: MFA verification and email fallback API

  Scenario: POST /mfa/verify without auth returns 401
    When I send a POST request to "/mfa/verify" with JSON
      """
      {"code": "123456", "method": "totp"}
      """
    Then the response status code should be 401

  Scenario: POST /mfa/email/send without auth returns 401
    When I send a POST request to "/mfa/email/send"
    Then the response status code should be 401

  Scenario: POST /mfa/email/verify without auth returns 401
    When I send a POST request to "/mfa/email/verify" with JSON
      """
      {"code": "123456"}
      """
    Then the response status code should be 401

  Scenario: POST /mfa/verify with auth but MFA not enabled returns 400
    Given a registered and verified user "mfa-verify@example.com" with password "securepassword123"
    And I am logged in as "mfa-verify@example.com" with password "securepassword123"
    When I send a POST request to "/mfa/verify" with JSON
      """
      {"code": "123456", "method": "totp"}
      """
    Then the response status code should be 400
    And the response body should contain "not enabled"

  Scenario: POST /mfa/email/send with auth but MFA not enabled returns 400
    Given a registered and verified user "mfa-email-send@example.com" with password "securepassword123"
    And I am logged in as "mfa-email-send@example.com" with password "securepassword123"
    When I send a POST request to "/mfa/email/send"
    Then the response status code should be 400
    And the response body should contain "not enabled"

  Scenario: POST /mfa/email/verify with auth but MFA not enabled returns 400
    Given a registered and verified user "mfa-email-verify@example.com" with password "securepassword123"
    And I am logged in as "mfa-email-verify@example.com" with password "securepassword123"
    When I send a POST request to "/mfa/email/verify" with JSON
      """
      {"code": "123456"}
      """
    Then the response status code should be 400
    And the response body should contain "not enabled"

  Scenario: POST /mfa/verify with valid TOTP code returns verified
    Given a user with MFA enabled
    When I send a POST request to "/mfa/verify" with JSON
      """
      {"code": "${mfa_totp_code}", "method": "totp"}
      """
    Then the response status code should be 200
    And the response should have JSON key "verified"
    And the response body should contain "true"
    And the response body should contain "totp"

  Scenario: POST /mfa/verify with valid backup code returns verified
    Given a user with MFA enabled
    When I send a POST request to "/mfa/verify" with JSON
      """
      {"code": "${mfa_backup_code}", "method": "backup"}
      """
    Then the response status code should be 200
    And the response should have JSON key "verified"
    And the response body should contain "backup"

  Scenario: POST /mfa/verify with wrong TOTP code returns 400
    Given a user with MFA enabled
    When I send a POST request to "/mfa/verify" with JSON
      """
      {"code": "000000", "method": "totp"}
      """
    Then the response status code should be 400
    And the response body should contain "Invalid TOTP"

  Scenario: POST /mfa/email/send with MFA enabled sends code
    Given a user with MFA enabled
    When I send a POST request to "/mfa/email/send"
    Then the response status code should be 200
    And the response body should contain "sent"
