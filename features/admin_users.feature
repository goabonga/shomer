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

  Scenario: GET /admin/users/{id} without auth returns 401
    When I send a GET request to "/admin/users/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: GET /admin/users/{id} with invalid UUID returns 400
    Given an admin user "admin-getbad@example.com" with password "securepassword123"
    And I am logged in as "admin-getbad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/users/not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid user ID"

  Scenario: GET /admin/users/{id} with admin scope returns user detail
    Given an admin user "admin-detail@example.com" with password "securepassword123"
    And I am logged in as "admin-detail@example.com" with password "securepassword123"
    When I send a GET request to "/admin/users"
    Then the response status code should be 200
    And the response should have JSON key "items"

  Scenario: POST /admin/users without auth returns 401
    When I send a POST request to "/admin/users" with JSON
      """
      {"email": "new-noauth@example.com", "password": "securepassword123"}
      """
    Then the response status code should be 401

  Scenario: POST /admin/users with admin scope creates user
    Given an admin user "admin-create@example.com" with password "securepassword123"
    And I am logged in as "admin-create@example.com" with password "securepassword123"
    When I send a POST request to "/admin/users" with JSON
      """
      {"email": "created-by-admin@example.com", "password": "securepassword123", "username": "newuser"}
      """
    Then the response status code should be 201
    And the response body should contain "created-by-admin@example.com"
    And the response body should contain "User created successfully"

  Scenario: PUT /admin/users/{id} without auth returns 401
    When I send a PUT request to "/admin/users/00000000-0000-0000-0000-000000000001" with JSON
      """
      {"is_active": false}
      """
    Then the response status code should be 401

  Scenario: DELETE /admin/users/{id} without auth returns 401
    When I send a DELETE request to "/admin/users/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401
