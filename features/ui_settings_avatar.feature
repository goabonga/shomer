Feature: Avatar on profile settings page

  Scenario: Profile page has picture URL field
    Given I register and verify "avatar-url@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "avatar-url@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    Then the page should contain "Profile"
    And the page should contain "Picture URL"
    And I take a screenshot named "settings_avatar_url"
