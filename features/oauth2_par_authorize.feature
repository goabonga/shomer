Feature: OAuth2 authorize with request_uri (RFC 9126)

  Scenario: Authorize with unknown request_uri renders error
    When I send a GET request to "/oauth2/authorize?client_id=bdd-full-client&request_uri=urn:ietf:params:oauth:request_uri:nonexistent"
    Then the response status code should be 400
    And the response body should contain "Unknown"

  Scenario: Authorize with request_uri but no client_id renders error
    When I send a GET request to "/oauth2/authorize?request_uri=urn:ietf:params:oauth:request_uri:abc"
    Then the response status code should be 400
    And the response body should contain "client_id is required"

  Scenario: Authorize with valid request_uri redirects to login
    Given a verified user and an OAuth2 client with all grants
    And a pushed authorization request for the OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-full-client&request_uri=${request_uri}"
    Then the response status code should be 200
    And the response body should contain "Login"

  Scenario: Authorize with used request_uri renders error (single-use)
    Given a verified user and an OAuth2 client with all grants
    And a pushed authorization request for the OAuth2 client
    When I send a GET request to "/oauth2/authorize?client_id=bdd-full-client&request_uri=${request_uri}"
    Then the response status code should be 200
    And the response body should contain "Login"
    When I send a GET request to "/oauth2/authorize?client_id=bdd-full-client&request_uri=${request_uri}"
    Then the response status code should be 400
    And the response body should contain "Unknown"
