Feature: Federation UI — social login buttons and error display

  Scenario: Login page renders without federation when no tenant
    When I open the page "/ui/login"
    Then the page should contain "Login"
    And the page should contain "Create an account"
    And I take a screenshot named "login_no_federation"

  Scenario: Login page displays federation error from callback
    When I open the page "/ui/login?error=federation_failed&message=User+denied+access"
    Then the page should contain "Login"
    And the page should contain "User denied access"
    And I take a screenshot named "login_federation_error"

  Scenario: Login page with tenant and IdP shows provider button
    Given a tenant with an identity provider
    When I open the page "/ui/login"
    Then the page should contain "Login"
    And I take a screenshot named "login_with_providers"
