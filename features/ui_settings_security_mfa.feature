Feature: Security settings with MFA status and Tokens link

  Scenario: Security page shows MFA disabled and setup link
    Given a registered and verified user "sec-mfa@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "sec-mfa@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Multi-Factor Authentication"
    And the page should contain "disabled"
    And the page should contain "Set Up MFA"
    And I take a screenshot named "settings_security_mfa_disabled"

  Scenario: Security settings nav includes Tokens link
    Given a registered and verified user "sec-nav@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "sec-nav@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Tokens"
    And the page should contain "Profile"
    And the page should contain "Emails"
    And I take a screenshot named "settings_security_nav"
