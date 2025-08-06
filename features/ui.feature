Feature: Home page

  Scenario: Home page displays the title
    When I open the page "/"
    Then the page title should be "Shomer"
    And the page should contain "OIDC/OAuth2 authentication service."
    And the page should contain the current version
    And I take a screenshot named "home_page"
