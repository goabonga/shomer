Feature: OAuth2 consent flow

  Scenario: Authorization without client_id shows error
    When I open the page "/oauth2/authorize?response_type=code&state=xyz"
    Then the page should contain "client_id"
    And I take a screenshot named "oauth2_missing_client_id"

  Scenario: Consent flow — user logs in and sees consent page
    Given an authenticated user with an OAuth2 client
    When I open the page "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid+profile&state=bddstate123"
    Then the page should contain "Login"
    When I fill "input[name='email']" with "oauth2-bdd@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page should contain "BDD Test App"
    And the page should contain "Authorize"
    And the page should contain "Verify your identity"
    And the page should contain "View your profile information"
    And the page should contain "Deny"
    And I take a screenshot named "oauth2_consent_page"

  Scenario: Consent flow — user approves and gets redirected with code
    Given an authenticated user with an OAuth2 client
    When I open the page "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid+profile&state=approvetest"
    Then the page should contain "Login"
    When I fill "input[name='email']" with "oauth2-bdd@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page should contain "Authorize"
    When I click the "Authorize" button
    Then the page URL should contain "code="
    And the page URL should contain "state=approvetest"
    And I take a screenshot named "oauth2_consent_approved"

  Scenario: Consent flow — user denies and gets redirected with error
    Given an authenticated user with an OAuth2 client
    When I open the page "/oauth2/authorize?client_id=bdd-test-client&redirect_uri=https://app.example.com/callback&response_type=code&scope=openid+profile&state=denytest"
    Then the page should contain "Login"
    When I fill "input[name='email']" with "oauth2-bdd@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page should contain "Authorize"
    When I click the "Deny" button
    Then the page URL should contain "error=access_denied"
    And the page URL should contain "state=denytest"
    And I take a screenshot named "oauth2_consent_denied"
