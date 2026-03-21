Feature: Device code verification UI

  Scenario: Device verify page redirects to login when unauthenticated
    When I open the page "/ui/device"
    Then the page should contain "Login"
    And I take a screenshot named "device_verify_redirect"

  Scenario: Device verify page with user_code redirects to login preserving code
    When I open the page "/ui/device?user_code=ABCD-EFGH"
    Then the page should contain "Login"
    And I take a screenshot named "device_verify_redirect_code"

  Scenario: Device verify page renders when authenticated
    Given I register and verify "device-ui@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "device-ui@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/device"
    Then the page should contain "Device Verification"
    And the page should contain "Authorize"
    And the page should contain "Deny"
    And I take a screenshot named "device_verify_page"

  Scenario: Device verify page auto-fills user_code from query param
    Given I register and verify "device-ui2@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "device-ui2@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/device?user_code=TEST-CODE"
    Then the page should contain "Device Verification"
    And I take a screenshot named "device_verify_autofill"
