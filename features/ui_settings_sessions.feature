Feature: Session management on security settings page

  Scenario: Security page displays session list with details
    Given I register and verify "sess-list@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "sess-list@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Active Sessions"
    And the page should contain "IP Address"
    And the page should contain "User Agent"
    And the page should contain "Last Activity"
    And the page should contain "Current"
    And the page should have an element "table.sessions-table"
    And I take a screenshot named "settings_sessions_list"

  Scenario: Current session shows Current badge instead of Revoke button
    Given I register and verify "sess-badge@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "sess-badge@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Current"
    And the page should have an element "span.badge.current"
    And I take a screenshot named "settings_sessions_current_badge"

  Scenario: Session list redirects to login when unauthenticated
    When I open the page "/ui/settings/security"
    Then the page should contain "Login"
    And I take a screenshot named "settings_sessions_redirect"
