Feature: Connected applications settings UI page

  Scenario: Applications page redirects to login when unauthenticated
    When I open the page "/ui/settings/applications"
    Then the page should contain "Login"
    And I take a screenshot named "applications_redirect_login"

  Scenario: Applications page renders when authenticated
    Given I register and verify "apps-ui@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "apps-ui@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/applications"
    Then the page should contain "Connected Applications"
    And the page should contain "No connected applications"
    And I take a screenshot named "applications_page_empty"

  Scenario: Applications page shows settings navigation
    Given I register and verify "apps-ui-nav@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "apps-ui-nav@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/applications"
    Then the page should contain "Profile"
    And the page should contain "Profile"
    And the page should contain "Emails"
    And the page should contain "Security"
    And the page should contain "Tokens"
    And the page should contain "Applications"
    And I take a screenshot named "applications_nav"

  Scenario: Applications link appears in all settings pages
    Given I register and verify "apps-ui-link@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "apps-ui-link@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings"
    Then the page should contain "Applications"
    When I navigate to "/ui/settings/profile"
    Then the page should contain "Applications"
    When I navigate to "/ui/settings/emails"
    Then the page should contain "Applications"
    When I navigate to "/ui/settings/security"
    Then the page should contain "Applications"
    And I take a screenshot named "applications_link_in_all"

  Scenario: Navigate to applications page via nav link
    Given I register and verify "apps-ui-click@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "apps-ui-click@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    And I click the "Applications" link
    Then the page URL should contain "/ui/settings/applications"
    And the page should contain "Connected Applications"
    And I take a screenshot named "applications_nav_click"
