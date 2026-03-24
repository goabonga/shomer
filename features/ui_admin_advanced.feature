Feature: Admin advanced UI pages (sessions, JWKS, roles, PATs, tenants)

  Scenario: Admin sessions page redirects to login when unauthenticated
    When I open the page "/ui/admin/sessions"
    Then the page should contain "Login"

  Scenario: Admin JWKS page redirects to login when unauthenticated
    When I open the page "/ui/admin/jwks"
    Then the page should contain "Login"

  Scenario: Admin roles page redirects to login when unauthenticated
    When I open the page "/ui/admin/roles"
    Then the page should contain "Login"

  Scenario: Admin PATs page redirects to login when unauthenticated
    When I open the page "/ui/admin/pats"
    Then the page should contain "Login"

  Scenario: Admin tenants page redirects to login when unauthenticated
    When I open the page "/ui/admin/tenants"
    Then the page should contain "Login"
