Feature: Admin tenants API

  # --- Tenants CRUD ---

  Scenario: GET /admin/tenants without auth returns 401
    When I send a GET request to "/admin/tenants"
    Then the response status code should be 401

  Scenario: GET /admin/tenants without admin scope returns 403
    Given a registered and verified user "tenant-noscope@example.com" with password "securepassword123"
    And I am logged in as "tenant-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/tenants"
    Then the response status code should be 403

  Scenario: GET /admin/tenants with admin scope returns tenant list
    Given an admin user "admin-tenants-list@example.com" with password "securepassword123"
    And I am logged in as "admin-tenants-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/tenants"
    Then the response status code should be 200
    And the response should have JSON key "items"
    And the response should have JSON key "total"

  Scenario: POST /admin/tenants without auth returns 401
    When I send a POST request to "/admin/tenants" with JSON
      """
      {"slug": "noauth-co", "name": "No Auth Co"}
      """
    Then the response status code should be 401

  Scenario: POST /admin/tenants with admin creates tenant
    Given an admin user "admin-tenants-create@example.com" with password "securepassword123"
    And I am logged in as "admin-tenants-create@example.com" with password "securepassword123"
    When I send a POST request to "/admin/tenants" with JSON
      """
      {"slug": "bdd-tenant", "name": "BDD Tenant", "display_name": "BDD Test Tenant"}
      """
    Then the response status code should be 201
    And the response body should contain "Tenant created successfully"
    And the response body should contain "bdd-tenant"

  # --- Tenant detail ---

  Scenario: GET /admin/tenants/{id} without auth returns 401
    When I send a GET request to "/admin/tenants/00000000-0000-0000-0000-000000000001"
    Then the response status code should be 401

  Scenario: GET /admin/tenants/{id} with invalid UUID returns 400
    Given an admin user "admin-tenants-bad@example.com" with password "securepassword123"
    And I am logged in as "admin-tenants-bad@example.com" with password "securepassword123"
    When I send a GET request to "/admin/tenants/not-a-uuid"
    Then the response status code should be 400

  # --- Members ---

  Scenario: GET /admin/tenants/{id}/members without auth returns 401
    When I send a GET request to "/admin/tenants/00000000-0000-0000-0000-000000000001/members"
    Then the response status code should be 401

  Scenario: POST /admin/tenants/{id}/members without auth returns 401
    When I send a POST request to "/admin/tenants/00000000-0000-0000-0000-000000000001/members" with JSON
      """
      {"user_id": "00000000-0000-0000-0000-000000000002"}
      """
    Then the response status code should be 401

  # --- Branding ---

  Scenario: PUT /admin/tenants/{id}/branding without auth returns 401
    When I send a PUT request to "/admin/tenants/00000000-0000-0000-0000-000000000001/branding" with JSON
      """
      {"primary_color": "#ff0000"}
      """
    Then the response status code should be 401

  # --- IdPs ---

  Scenario: GET /admin/tenants/{id}/idps without auth returns 401
    When I send a GET request to "/admin/tenants/00000000-0000-0000-0000-000000000001/idps"
    Then the response status code should be 401

  Scenario: POST /admin/tenants/{id}/idps without auth returns 401
    When I send a POST request to "/admin/tenants/00000000-0000-0000-0000-000000000001/idps" with JSON
      """
      {"name": "Google", "provider_type": "google", "client_id": "goog-123"}
      """
    Then the response status code should be 401

  # --- Domains ---

  Scenario: GET /admin/tenants/{id}/domains without auth returns 401
    When I send a GET request to "/admin/tenants/00000000-0000-0000-0000-000000000001/domains"
    Then the response status code should be 401

  Scenario: PUT /admin/tenants/{id}/domains without auth returns 401
    When I send a PUT request to "/admin/tenants/00000000-0000-0000-0000-000000000001/domains" with JSON
      """
      {"custom_domain": "auth.example.com"}
      """
    Then the response status code should be 401
