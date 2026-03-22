Feature: Federation providers API

  Scenario: GET /federation/providers without tenant returns 400
    When I send a GET request to "/federation/providers"
    Then the response status code should be 400
    And the response body should contain "Tenant not specified"

  Scenario: GET /federation/providers with unknown tenant returns empty list
    When I send a GET request to "/federation/providers?tenant_slug=nonexistent"
    Then the response status code should be 200
    And the response should have JSON key "providers"
    And the response body should contain "local_login_enabled"

  Scenario: GET /federation/providers with tenant returns IdP list
    Given a tenant with an identity provider
    When I send a GET request to "/federation/providers?tenant_slug=${federation_tenant_slug}"
    Then the response status code should be 200
    And the response body should contain "BDD Google"
    And the response body should contain "google"
    And the response body should contain "Continue with"

  Scenario: GET /federation/authorize without tenant context returns 400
    When I send a GET request to "/federation/00000000-0000-0000-0000-000000000001/authorize"
    Then the response status code should be 400
    And the response body should contain "Tenant context required"
