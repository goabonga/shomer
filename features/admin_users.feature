Feature: Admin users API

  Scenario: GET /admin/users without auth returns 401
    When I send a GET request to "/admin/users"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/users without admin scope returns 403
    Given a registered and verified user "admin-noscope@example.com" with password "securepassword123"
    And I am logged in as "admin-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/users"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/users with admin scope returns user list
    Given an admin user "admin-list@example.com" with password "securepassword123"
    And I am logged in as "admin-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/users"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"
    And the response should have JSON key "page"
    And the response should have JSON key "page_size"
