Feature: User logout

  Scenario: Logout without session returns success
    When I send a POST request to "/auth/logout"
    Then the response status code should be 200
    And the response body should contain "Logged out"

  Scenario: Logout with logout_all returns success
    When I send a POST request to "/auth/logout" with JSON
      """
      {"logout_all": true}
      """
    Then the response status code should be 200
    And the response body should contain "Logged out"
