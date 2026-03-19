Feature: OAuth2 consent flow

  Scenario: Authorization without client_id shows error
    When I open the page "/oauth2/authorize?response_type=code&state=xyz"
    Then the page should contain "client_id"
    And I take a screenshot named "oauth2_missing_client_id"

  Scenario: Consent flow — user logs in and approves
    Given an authenticated user with an OAuth2 client
    When I open the page "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid+profile&state=bddstate123"
    Then the page should contain "Login"
    When I fill "input[name='email']" with "oauth2-bdd@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then I take a screenshot named "oauth2_debug_after_click"
