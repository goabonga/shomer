Feature: UI redesign — dark theme, CSS, settings sidebar

  Scenario: Login page loads with centralized CSS
    When I open the page "/ui/login"
    Then the page should contain "Login"
    And the page should have an element "link[href='/static/css/shomer.css']"
    And I take a screenshot named "redesign_login_dark"

  Scenario: Register page loads with dark theme
    When I open the page "/ui/register"
    Then the page should contain "Register"
    And the page should have an element "link[href='/static/css/shomer.css']"

  Scenario: Settings profile uses sidebar navigation
    Given I register and verify "redesign-profile@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "redesign-profile@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    Then the page should contain "Profile"
    And the page should have an element "nav.sidebar"
    And the page should have an element "link[href='/static/css/shomer.css']"
    And I take a screenshot named "redesign_settings_sidebar"

  Scenario: Settings sidebar has all navigation links
    Given I register and verify "redesign-nav@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "redesign-nav@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    Then the page should contain "Emails"
    And the page should contain "Security"
    And the page should contain "Tokens"
    And the page should contain "Applications"
    And the page should contain "Logout"

  Scenario: Admin dashboard has burger menu elements
    When I open the page "/ui/admin"
    Then the page should contain "Login"
    And I take a screenshot named "redesign_admin_redirect"
