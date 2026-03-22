Feature: Federation callback endpoint

  Scenario: Callback with IdP error redirects to login
    When I send a GET request to "/federation/callback?error=access_denied&error_description=User+denied"
    Then the response status code should be 200
    And the response body should contain "Login"

  Scenario: Callback without code or state redirects to login
    When I send a GET request to "/federation/callback"
    Then the response status code should be 200
    And the response body should contain "Login"

  Scenario: Callback with invalid state redirects to login
    When I send a GET request to "/federation/callback?code=test&state=invalid!!!"
    Then the response status code should be 200
    And the response body should contain "Login"
