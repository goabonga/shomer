Feature: OAuth2 authorize with request param (RFC 9101 JAR)

  Scenario: Authorize with request param but no client_id renders error
    When I send a GET request to "/oauth2/authorize?request=eyJhbGciOiJSUzI1NiJ9.eyJ0ZXN0IjoidmFsdWUifQ.invalid"
    Then the response status code should be 400
    And the response body should contain "client_id is required"

  Scenario: Authorize with request param and unknown client renders error
    When I send a GET request to "/oauth2/authorize?client_id=nonexistent&request=eyJhbGciOiJSUzI1NiJ9.eyJ0ZXN0IjoidmFsdWUifQ.invalid"
    Then the response status code should be 400
    And the response body should contain "Unknown client_id"

  Scenario: Authorize with request param and client without JWKS renders error
    Given a verified user and an OAuth2 client with all grants
    When I send a GET request to "/oauth2/authorize?client_id=bdd-full-client&request=eyJhbGciOiJSUzI1NiJ9.eyJ0ZXN0IjoidmFsdWUifQ.invalid"
    Then the response status code should be 400
    And the response body should contain "no JWKS registered"
