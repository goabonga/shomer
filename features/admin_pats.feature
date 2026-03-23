Feature: Admin PATs API

  Scenario: GET /admin/pats without auth returns 401
    When I send a GET request to "/admin/pats"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/pats without admin scope returns 403
    Given a registered and verified user "pats-noscope@example.com" with password "securepassword123"
    And I am logged in as "pats-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/pats"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/pats with admin scope returns PAT list
    Given an admin user "admin-pats-list@example.com" with password "securepassword123"
    And I am logged in as "admin-pats-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/pats"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"
    And the response should have JSON key "page"

  Scenario: GET /admin/pats with invalid user_id filter returns 400
    Given an admin user "admin-pats-bad@example.com" with password "securepassword123"
    And I am logged in as "admin-pats-bad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/pats?user_id=not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid user_id"

  Scenario: GET /admin/pats/{id} without auth returns 401
    When I send a GET request to "/admin/pats/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: GET /admin/pats/{id} with invalid UUID returns 400
    Given an admin user "admin-pats-getbad@example.com" with password "securepassword123"
    And I am logged in as "admin-pats-getbad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/pats/not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid PAT ID"

  Scenario: DELETE /admin/pats/{id} without auth returns 401
    When I send a DELETE request to "/admin/pats/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401
