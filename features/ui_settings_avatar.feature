Feature: Avatar upload on profile settings page

  Scenario: Profile page shows avatar fallback when no avatar uploaded
    Given I register and verify "avatar-fallback@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "avatar-fallback@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    Then the page should have an element ".avatar-fallback"
    And the page should have an element "input[name='avatar']"
    And the page should contain "JPEG, PNG, GIF, or WebP"
    And I take a screenshot named "settings_avatar_fallback"

  Scenario: Upload valid avatar image shows success message
    Given I register and verify "avatar-upload@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "avatar-upload@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    And I attach file "test_avatar.png" to "input[name='avatar']"
    And I click the "Upload" button
    Then the page should contain "Avatar updated successfully"
    And the page should have an element ".avatar-img"
    And I take a screenshot named "settings_avatar_uploaded"

  Scenario: Upload invalid file type shows error message
    Given I register and verify "avatar-invalid@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "avatar-invalid@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/profile"
    And I attach file "test_file.txt" to "input[name='avatar']"
    And I click the "Upload" button
    Then the page should contain "Invalid file type"
    And I take a screenshot named "settings_avatar_invalid_type"
