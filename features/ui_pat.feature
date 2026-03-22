Feature: PAT management UI page

  Scenario: PAT page redirects to login when unauthenticated
    When I open the page "/ui/settings/pats"
    Then the page should contain "Login"
    And I take a screenshot named "pat_redirect_login"

  Scenario: PAT page renders when authenticated
    Given I register and verify "pat-ui@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-ui@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    Then the page should contain "Personal Access Tokens"
    And the page should contain "Create New Token"
    And I take a screenshot named "pat_page"

  Scenario: Create PAT shows token value
    Given I register and verify "pat-ui-create@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-ui-create@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "my-ci-key"
    And I fill "input[name='scopes']" with "api:read"
    And I click the "Create Token" button
    Then the page should contain "shm_pat_"
    And the page should contain "Token Created"
    And the page should contain "my-ci-key"
    And I take a screenshot named "pat_created"

  Scenario: PAT list shows created tokens
    Given I register and verify "pat-ui-list@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-ui-list@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "list-key"
    And I click the "Create Token" button
    Then the page should contain "list-key"
    And the page should contain "Active"
    And I take a screenshot named "pat_list"

  Scenario: Settings navigation includes Tokens link
    Given I register and verify "pat-ui-nav@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-ui-nav@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    Then the page should contain "Profile"
    And the page should contain "Emails"
    And the page should contain "Security"
    And the page should contain "Tokens"
    And I take a screenshot named "pat_nav"
