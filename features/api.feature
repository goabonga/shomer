Feature: API health checks

  Scenario: Liveness endpoint returns ok
    When I send a GET request to "/liveness"
    Then the response status code should be 200
    And the response body should contain "status"

  Scenario: Readiness endpoint returns ready
    When I send a GET request to "/readiness"
    Then the response status code should be 200
    And the response body should contain "ready"
