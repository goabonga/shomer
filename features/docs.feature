Feature: Documentation endpoints

  Scenario: Swagger UI is accessible
    When I send a GET request to "/docs"
    Then the response status code should be 200
    And the response content type should be html

  Scenario: ReDoc is accessible
    When I send a GET request to "/redoc"
    Then the response status code should be 200
    And the response content type should be html

  Scenario: OpenAPI JSON is accessible
    When I send a GET request to "/openapi.json"
    Then the response status code should be 200
    And the response body should contain "openapi"
