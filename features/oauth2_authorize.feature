Feature: OAuth2 authorization endpoint

  Scenario: Missing client_id without redirect_uri returns 400
    When I send a GET request to "/oauth2/authorize?response_type=code"
    Then the response status code should be 400
    And the response body should contain "client_id"

  Scenario: Missing state without redirect_uri returns 400
    When I send a GET request to "/oauth2/authorize?client_id=unknown&response_type=code"
    Then the response status code should be 400
