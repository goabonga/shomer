Feature: Admin dashboard UI page

  Scenario: Admin dashboard redirects to login when unauthenticated
    When I open the page "/ui/admin"
    Then the page should contain "Login"
    And I take a screenshot named "admin_dashboard_redirect"

  Scenario: Admin dashboard redirects non-admin users to login
    Given I register and verify "nonadmin-dash@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "nonadmin-dash@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/admin"
    Then the page should contain "Login"
    And I take a screenshot named "admin_dashboard_nonadmin"
