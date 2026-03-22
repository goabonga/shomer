Feature: Federation providers API

  Scenario: GET /federation/providers without tenant returns 400
    When I send a GET request to "/federation/providers"
    Then the response status code should be 400
    And the response body should contain "Tenant not specified"

  Scenario: GET /federation/providers with tenant_slug returns empty list
    When I send a GET request to "/federation/providers?tenant_slug=nonexistent"
    Then the response status code should be 200
    And the response should have JSON key "providers"
    And the response body should contain "local_login_enabled"
