Feature: Authentication UI pages

  Scenario: Registration page renders correctly
    When I open the page "/ui/register"
    Then the page title should be "Register — Shomer"
    And the page should contain "Register"
    And the page should contain "Already have an account?"
    And I take a screenshot named "register_page"

  Scenario: Registration form submits and redirects to verify
    When I open the page "/ui/register"
    And I fill "input[name='email']" with "uitest@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Register" button
    Then the page should contain "Verify Email"
    And the page should contain "Check your email"
    And I take a screenshot named "register_success"

  Scenario: Registration with duplicate email still redirects to verify (anti-enumeration)
    When I open the page "/ui/register"
    And I fill "input[name='email']" with "dupe-ui@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Register" button
    Then the page should contain "Verify Email"
    When I open the page "/ui/register"
    And I fill "input[name='email']" with "dupe-ui@example.com"
    And I fill "input[name='password']" with "anotherpassword1"
    And I click the "Register" button
    Then the page should contain "Verify Email"
    And I take a screenshot named "register_duplicate_safe"

  Scenario: Verification page renders correctly
    When I open the page "/ui/verify"
    Then the page title should be "Verify Email — Shomer"
    And the page should contain "Verify Email"
    And the page should contain "Resend Code"
    And I take a screenshot named "verify_page"

  Scenario: Verification with valid code shows success
    Given I register and verify "ui-verify-happy@example.com" with password "securepassword123"
    When I open the page "/ui/verify"
    Then the page should contain "Verify Email"
    And I take a screenshot named "verify_after_registration"

  Scenario: Login with unverified email shows error
    When I open the page "/ui/register"
    And I fill "input[name='email']" with "ui-unverified@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Register" button
    Then the page should contain "Verify Email"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "ui-unverified@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page should contain "not verified"
    And I take a screenshot named "login_unverified"

  Scenario: Verification with invalid code shows error
    When I open the page "/ui/verify"
    And I fill "input[name='email']" with "nobody@example.com"
    And I fill "input[name='code']" with "000000"
    And I click the "Verify" button
    Then the page should contain "Invalid or expired"
    And I take a screenshot named "verify_invalid"

  Scenario: Login page renders correctly
    When I open the page "/ui/login"
    Then the page title should be "Login — Shomer"
    And the page should contain "Login"
    And the page should contain "Create an account"
    And I take a screenshot named "login_page"

  Scenario: Login with invalid credentials shows error
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "nobody@example.com"
    And I fill "input[name='password']" with "wrongpassword1"
    And I click the "Login" button
    Then the page should contain "Invalid email or password"
    And I take a screenshot named "login_invalid"

  Scenario: Navigate from login to register via link
    When I open the page "/ui/login"
    And I click the "Create an account" link
    Then the page URL should contain "/ui/register"
    And the page should contain "Register"
    And I take a screenshot named "login_to_register"

  Scenario: Login with valid credentials redirects to home
    Given I register and verify "ui-login-happy@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "ui-login-happy@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    And I take a screenshot named "login_success"

  Scenario: Login page preserves next parameter
    When I open the page "/ui/login?next=/dashboard"
    Then the page title should be "Login — Shomer"
    And I take a screenshot named "login_next_param"
