Feature: OIDC UserInfo endpoint

  Scenario: GET /userinfo without Authorization returns 401
    When I send a GET request to "/userinfo"
    Then the response status code should be 401

  Scenario: POST /userinfo without Authorization returns 401
    When I send a POST request to "/userinfo"
    Then the response status code should be 401

  Scenario: GET /userinfo with valid Bearer token returns sub
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a GET request to "/userinfo"
    Then the response status code should be 200
    And the response should have JSON key "sub"

  Scenario: GET /userinfo with valid Bearer token returns email
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a GET request to "/userinfo"
    Then the response status code should be 200
    And the response body should contain "email"

  Scenario: POST /userinfo with valid Bearer token returns sub
    Given a verified user and an OAuth2 client with all grants
    And I have a Bearer token for the OAuth2 client
    When I send a POST request to "/userinfo"
    Then the response status code should be 200
    And the response should have JSON key "sub"
