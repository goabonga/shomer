Feature: Admin dashboard API

  Scenario: GET /admin/dashboard without auth returns 401
    When I send a GET request to "/admin/dashboard"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/dashboard without admin scope returns 403
    Given a registered and verified user "dash-noscope@example.com" with password "securepassword123"
    And I am logged in as "dash-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/dashboard"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/dashboard with admin scope returns statistics
    Given an admin user "admin-dash@example.com" with password "securepassword123"
    And I am logged in as "admin-dash@example.com" with password "securepassword123"
    When I send a GET request to "/admin/dashboard"
    Then the response status code should be 200
    And the response should have JSON key "users"
    And the response should have JSON key "sessions"
    And the response should have JSON key "clients"
    And the response should have JSON key "tokens"
    And the response should have JSON key "mfa"
