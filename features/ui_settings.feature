Feature: User settings UI pages

  Scenario: Profile settings redirects to login when unauthenticated
    When I open the page "/ui/settings/profile"
    Then the page should contain "Login"
    And I take a screenshot named "settings_profile_redirect"

  Scenario: Email settings redirects to login when unauthenticated
    When I open the page "/ui/settings/emails"
    Then the page should contain "Login"
    And I take a screenshot named "settings_emails_redirect"

  Scenario: Security settings redirects to login when unauthenticated
    When I open the page "/ui/settings/security"
    Then the page should contain "Login"
    And I take a screenshot named "settings_security_redirect"

  Scenario: Profile settings page renders all sections when authenticated
    Given I register and verify "settings-user@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "settings-user@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    Then the page should contain "Settings"
    And the page should contain "Profile"
    And the page should contain "Identity"
    And the page should contain "Personal Information"
    And the page should contain "Contact"
    And the page should contain "Picture URL"
    And the page should contain "Address"
    And the page should contain "Save changes"
    And the page should have an element "input[name='nickname']"
    And the page should have an element "input[name='given_name']"
    And the page should have an element "input[name='family_name']"
    And the page should have an element "input[name='middle_name']"
    And the page should have an element "input[name='preferred_username']"
    And the page should have an element "select[name='gender']"
    And I take a screenshot named "settings_profile_page"

  Scenario: Profile form saves and shows success message
    Given I register and verify "settings-save@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "settings-save@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    And I fill "input[name='nickname']" with "TestNick"
    And I fill "input[name='given_name']" with "John"
    And I fill "input[name='family_name']" with "Doe"
    And I click the "Save changes" button
    Then the page should contain "Profile updated successfully"
    And I take a screenshot named "settings_profile_saved"

  Scenario: Navigate between settings sections
    Given I register and verify "settings-nav@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "settings-nav@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    Then the page should contain "Email Addresses"
    And I take a screenshot named "settings_emails_page"

  Scenario: Security settings shows active sessions
    Given I register and verify "settings-sec@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "settings-sec@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Security"
    And the page should contain "Active Sessions"
    And the page should contain "Change Password"
    And I take a screenshot named "settings_security_page"
