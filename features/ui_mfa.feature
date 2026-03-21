Feature: MFA UI pages

  Scenario: MFA setup page redirects to login when unauthenticated
    When I open the page "/ui/mfa/setup"
    Then the page should contain "Login"
    And I take a screenshot named "mfa_setup_redirect"

  Scenario: MFA challenge page without token redirects to login
    When I open the page "/ui/mfa/challenge"
    Then the page should contain "Login"
    And I take a screenshot named "mfa_challenge_redirect"

  Scenario: MFA setup page renders when authenticated
    Given I register and verify "mfa-ui-setup@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "mfa-ui-setup@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/mfa/setup"
    Then the page should contain "MFA Setup"
    And the page should contain "Set Up MFA"
    And I take a screenshot named "mfa_setup_page"

  Scenario: MFA setup generates QR code and secret
    Given I register and verify "mfa-ui-qr@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "mfa-ui-qr@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/mfa/setup"
    And I click the "Set Up MFA" button
    Then the page should contain "authenticator app"
    And the page should contain "Verify"
    And I take a screenshot named "mfa_setup_qr"

  Scenario: MFA challenge page renders with token
    When I open the page "/ui/mfa/challenge?mfa_token=test-token&method=totp"
    Then the page should contain "MFA Verification"
    And the page should contain "authenticator app"
    And the page should contain "Verify"
    And I take a screenshot named "mfa_challenge_page"

  Scenario: MFA challenge page shows backup code option
    When I open the page "/ui/mfa/challenge?mfa_token=test-token&method=backup"
    Then the page should contain "MFA Verification"
    And the page should contain "backup code"
    And I take a screenshot named "mfa_challenge_backup"

  Scenario: MFA challenge page shows email code option
    When I open the page "/ui/mfa/challenge?mfa_token=test-token&method=email"
    Then the page should contain "MFA Verification"
    And the page should contain "email"
    And I take a screenshot named "mfa_challenge_email"
