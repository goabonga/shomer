Feature: Admin OAuth2 clients API

  Scenario: GET /admin/clients without auth returns 401
    When I send a GET request to "/admin/clients"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/clients without admin scope returns 403
    Given a registered and verified user "client-noscope@example.com" with password "securepassword123"
    And I am logged in as "client-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/clients"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/clients with admin scope returns client list
    Given an admin user "admin-clients-list@example.com" with password "securepassword123"
    And I am logged in as "admin-clients-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/clients"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"
    And the response should have JSON key "page"

  Scenario: GET /admin/clients/{id} without auth returns 401
    When I send a GET request to "/admin/clients/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: GET /admin/clients/{id} with invalid UUID returns 400
    Given an admin user "admin-clients-bad@example.com" with password "securepassword123"
    And I am logged in as "admin-clients-bad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/clients/not-a-uuid"
    Then the response status code should be 400
    And the response body should contain "Invalid client ID"

  Scenario: POST /admin/clients without auth returns 401
    When I send a POST request to "/admin/clients" with JSON
      """
      {"client_name": "No Auth App", "client_type": "confidential"}
      """
    Then the response status code should be 401

  Scenario: POST /admin/clients with admin scope creates client
    Given an admin user "admin-clients-create@example.com" with password "securepassword123"
    And I am logged in as "admin-clients-create@example.com" with password "securepassword123"
    When I send a POST request to "/admin/clients" with JSON
      """
      {"client_name": "BDD Test Client", "client_type": "confidential", "redirect_uris": ["https://bdd.example.com/cb"], "grant_types": ["authorization_code"], "scopes": ["openid"]}
      """
    Then the response status code should be 201
    And the response body should contain "BDD Test Client"
    And the response body should contain "Client created successfully"
    And the response should have JSON key "client_id"
    And the response should have JSON key "client_secret"

  Scenario: PUT /admin/clients/{id} without auth returns 401
    When I send a PUT request to "/admin/clients/00000000-0000-0000-0000-000000000001" with JSON
      """
      {"client_name": "Updated"}
      """
    Then the response status code should be 401

  Scenario: DELETE /admin/clients/{id} without auth returns 401
    When I send a DELETE request to "/admin/clients/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401
