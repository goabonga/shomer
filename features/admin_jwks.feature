Feature: Admin JWKS API

  Scenario: GET /admin/jwks without auth returns 401
    When I send a GET request to "/admin/jwks"
    Then the response status code should be 401
    And the response body should contain "Authentication required"

  Scenario: GET /admin/jwks without admin scope returns 403
    Given a registered and verified user "jwks-noscope@example.com" with password "securepassword123"
    And I am logged in as "jwks-noscope@example.com" with password "securepassword123"
    When I send a GET request to "/admin/jwks"
    Then the response status code should be 403
    And the response body should contain "Insufficient permissions"

  Scenario: GET /admin/jwks with admin scope returns key list
    Given an admin user "admin-jwks-list@example.com" with password "securepassword123"
    And I am logged in as "admin-jwks-list@example.com" with password "securepassword123"
    When I send a GET request to "/admin/jwks"
    Then the response status code should be 200
    And the response should have JSON key "keys"
    And the response should have JSON key "total"

  Scenario: GET /admin/jwks/{kid} without auth returns 401
    When I send a GET request to "/admin/jwks/nonexistent-kid"
    Then the response status code should be 401

  Scenario: GET /admin/jwks/{kid} not found returns 404
    Given an admin user "admin-jwks-get@example.com" with password "securepassword123"
    And I am logged in as "admin-jwks-get@example.com" with password "securepassword123"
    When I send a GET request to "/admin/jwks/nonexistent-kid"
    Then the response status code should be 404
    And the response body should contain "Key not found"

  Scenario: POST /admin/jwks/rotate without auth returns 401
    When I send a POST request to "/admin/jwks/rotate"
    Then the response status code should be 401

  Scenario: DELETE /admin/jwks/{kid} without auth returns 401
    When I send a DELETE request to "/admin/jwks/some-kid"
    Then the response status code should be 401
