Feature: Password management UI pages

  Scenario: Forgot password page renders correctly
    When I open the page "/ui/password/reset"
    Then the page title should be "Forgot Password — Shomer"
    And the page should contain "Forgot Password"
    And the page should contain "Send Reset Link"
    And the page should contain "Back to login"
    And I take a screenshot named "forgot_password_page"

  Scenario: Forgot password form submits and shows success
    When I open the page "/ui/password/reset"
    And I fill "input[name='email']" with "anyone@example.com"
    And I click the "Send Reset Link" button
    Then the page should contain "reset link has been sent"
    And I take a screenshot named "forgot_password_success"

  Scenario: Navigate from forgot password to login via link
    When I open the page "/ui/password/reset"
    And I click the "Back to login" link
    Then the page URL should contain "/ui/login"
    And the page should contain "Login"
    And I take a screenshot named "forgot_to_login"

  Scenario: Reset password page renders correctly
    When I open the page "/ui/password/reset-verify"
    Then the page title should be "Reset Password — Shomer"
    And the page should contain "Reset Password"
    And the page should contain "Set New Password"
    And I take a screenshot named "reset_password_page"

  Scenario: Reset password with invalid token shows error
    When I open the page "/ui/password/reset-verify?token=not-a-uuid"
    And I fill "input[name='new_password']" with "newstrongpassword"
    And I click the "Set New Password" button
    Then the page should contain "Invalid reset token"
    And I take a screenshot named "reset_password_invalid_token"

  Scenario: Change password page renders correctly
    When I open the page "/ui/password/change"
    Then the page title should be "Change Password — Shomer"
    And the page should contain "Change Password"
    And I take a screenshot named "change_password_page"

  Scenario: Change password with valid session shows success
    Given I register and verify "ui-change-pw@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "ui-change-pw@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/password/change"
    And I fill "input[name='current_password']" with "securepassword123"
    And I fill "input[name='new_password']" with "newstrongpassword1"
    And I click the "Change Password" button
    Then the page should contain "Password changed"
    And I take a screenshot named "change_password_success"

  Scenario: Change password without session shows error
    When I open the page "/ui/password/change"
    And I fill "input[name='current_password']" with "oldpassword"
    And I fill "input[name='new_password']" with "newpassword1"
    And I click the "Change Password" button
    Then the page should contain "Authentication required"
    And I take a screenshot named "change_password_no_session"
