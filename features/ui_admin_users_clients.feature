Feature: Admin users and clients UI pages

  # --- Users ---

  Scenario: Admin users list redirects to login when unauthenticated
    When I open the page "/ui/admin/users"
    Then the page should contain "Login"
    And I take a screenshot named "admin_users_list_redirect"

  Scenario: Admin user create form redirects to login when unauthenticated
    When I open the page "/ui/admin/users/new"
    Then the page should contain "Login"

  Scenario: Admin users list redirects non-admin to login
    Given I register and verify "nonadmin-userslist@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "nonadmin-userslist@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/admin/users"
    Then the page should contain "Login"

  # --- Clients ---

  Scenario: Admin clients list redirects to login when unauthenticated
    When I open the page "/ui/admin/clients"
    Then the page should contain "Login"
    And I take a screenshot named "admin_clients_list_redirect"

  Scenario: Admin client create form redirects to login when unauthenticated
    When I open the page "/ui/admin/clients/new"
    Then the page should contain "Login"

  Scenario: Admin clients list redirects non-admin to login
    Given I register and verify "nonadmin-clientslist@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "nonadmin-clientslist@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/admin/clients"
    Then the page should contain "Login"
