Feature: Admin roles and scopes API

  # --- Scopes ---

  Scenario: GET /admin/scopes without auth returns 401
    When I send a GET request to "/admin/scopes"
    Then the response status code should be 401

  Scenario: GET /admin/scopes without admin scope returns 403
    Given a registered and verified user "rbac-noscope@example.com" with password "securepassword123"
    And I am logged in as "rbac-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/scopes"
    Then the response status code should be 403

  Scenario: GET /admin/scopes with admin scope returns scope list
    Given an admin user "admin-rbac-scopes@example.com" with password "securepassword123"
    And I am logged in as "admin-rbac-scopes@example.com" with password "securepassword123"
    When I send a GET request to "/admin/scopes"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"

  Scenario: POST /admin/scopes without auth returns 401
    When I send a POST request to "/admin/scopes" with JSON
      """
      {"name": "test:scope:noauth"}
      """
    Then the response status code should be 401

  Scenario: POST /admin/scopes with admin creates scope
    Given an admin user "admin-rbac-create-scope@example.com" with password "securepassword123"
    And I am logged in as "admin-rbac-create-scope@example.com" with password "securepassword123"
    When I send a POST request to "/admin/scopes" with JSON
      """
      {"name": "bdd:test:scope", "description": "BDD test scope"}
      """
    Then the response status code should be 201
    And the response body should contain "Scope created successfully"
    And the response body should contain "bdd:test:scope"

  # --- Roles ---

  Scenario: GET /admin/roles without auth returns 401
    When I send a GET request to "/admin/roles"
    Then the response status code should be 401

  Scenario: GET /admin/roles with admin scope returns role list
    Given an admin user "admin-rbac-roles@example.com" with password "securepassword123"
    And I am logged in as "admin-rbac-roles@example.com" with password "securepassword123"
    When I send a GET request to "/admin/roles"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"

  Scenario: POST /admin/roles without auth returns 401
    When I send a POST request to "/admin/roles" with JSON
      """
      {"name": "test-role-noauth"}
      """
    Then the response status code should be 401

  Scenario: POST /admin/roles with admin creates role
    Given an admin user "admin-rbac-create-role@example.com" with password "securepassword123"
    And I am logged in as "admin-rbac-create-role@example.com" with password "securepassword123"
    When I send a POST request to "/admin/roles" with JSON
      """
      {"name": "bdd-test-role", "description": "BDD test role"}
      """
    Then the response status code should be 201
    And the response body should contain "Role created successfully"
    And the response body should contain "bdd-test-role"

  # --- Assignments ---

  Scenario: POST /admin/users/{id}/roles/{role_id} without auth returns 401
    When I send a POST request to "/admin/users/00000000-0000-0000-0000-000000000001/roles/00000000-0000-0000-0000-000000000002"
    Then the response status code should be 401

  Scenario: DELETE /admin/users/{id}/roles/{role_id} without auth returns 401
    When I send a DELETE request to "/admin/users/00000000-0000-0000-0000-000000000001/roles/00000000-0000-0000-0000-000000000002"
    Then the response status code should be 401

  Scenario: POST /admin/roles/{id}/scopes/{scope_id} without auth returns 401
    When I send a POST request to "/admin/roles/00000000-0000-0000-0000-000000000001/scopes/00000000-0000-0000-0000-000000000002"
    Then the response status code should be 401

  Scenario: DELETE /admin/roles/{id}/scopes/{scope_id} without auth returns 401
    When I send a DELETE request to "/admin/roles/00000000-0000-0000-0000-000000000001/scopes/00000000-0000-0000-0000-000000000002"
    Then the response status code should be 401
