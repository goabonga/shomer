Feature: Admin sessions API

  Scenario: GET /admin/sessions without auth returns 401
    When I send a GET request to "/admin/sessions"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/sessions without admin scope returns 403
    Given a registered and verified user "sess-noscope@example.com" with password "securepassword123"
    And I am logged in as "sess-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/sessions"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/sessions with admin scope returns session list
    Given an admin user "admin-sess-list@example.com" with password "securepassword123"
    And I am logged in as "admin-sess-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/sessions"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"
    And the response should have JSON key "page"

  Scenario: GET /admin/sessions with invalid user_id filter returns 400
    Given an admin user "admin-sess-bad@example.com" with password "securepassword123"
    And I am logged in as "admin-sess-bad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/sessions?user_id=not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid user_id"

  Scenario: GET /admin/sessions/{id} without auth returns 401
    When I send a GET request to "/admin/sessions/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: GET /admin/sessions/{id} with invalid UUID returns 400
    Given an admin user "admin-sess-getbad@example.com" with password "securepassword123"
    And I am logged in as "admin-sess-getbad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/sessions/not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid session ID"

  Scenario: DELETE /admin/sessions/{id} without auth returns 401
    When I send a DELETE request to "/admin/sessions/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: DELETE /admin/sessions/users/{user_id} without auth returns 401
    When I send a DELETE request to "/admin/sessions/users/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401
