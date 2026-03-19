Feature: OAuth2 error pages

  Scenario: Missing client_id shows error page
    When I open the page "/oauth2/authorize?response_type=code&state=xyz"
    Then the page should contain "Authorization Error"
    And the page should contain "client_id"
    And the page should contain "Back to Home"
    And I take a screenshot named "oauth2_error_missing_client_id"

  Scenario: Unknown client_id shows error with description
    When I open the page "/oauth2/authorize?client_id=nonexistent&redirect_uri=https://evil.com&response_type=code&state=abc"
    Then the page should contain "Authorization Error"
    And the page should contain "Unknown client_id"
    And the page should contain "invalid_request"
    And I take a screenshot named "oauth2_error_unknown_client"

  Scenario: Missing state shows error page
    When I open the page "/oauth2/authorize?client_id=unknown&response_type=code"
    Then the page should contain "Authorization Error"
    And the page should contain "invalid_request"
    And I take a screenshot named "oauth2_error_missing_state"

  Scenario: Error page has link back to home
    When I open the page "/oauth2/authorize?response_type=code&state=xyz"
    Then the page should contain "Back to Home"
    When I click the "Back to Home" link
    Then the page URL should contain "/"
    And I take a screenshot named "oauth2_error_back_to_home"
