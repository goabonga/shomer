Feature: Email management in settings UI

  Scenario: Email settings page shows primary email with badges
    Given I register and verify "emails-page@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-page@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    Then the page should contain "Email Addresses"
    And the page should contain "emails-page@example.com"
    And the page should contain "Primary"
    And the page should contain "Verified"
    And the page should have an element "input[name='email'][type='email']"
    And I take a screenshot named "settings_emails_list"

  Scenario: Add email form is present on the page
    Given I register and verify "emails-form@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-form@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    Then the page should contain "Add Email"
    And the page should have an element "input[name='email'][placeholder='new@example.com']"
    And the page should have an element "button:has-text('Add Email')"
    And I take a screenshot named "settings_emails_add_form"

  Scenario: Add a new email shows success message
    Given I register and verify "emails-add@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-add@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    And I fill "input[name='email'][type='email']" with "newemail-add@example.com"
    And I click the "Add Email" button
    Then the page should contain "Email added"
    And the page should contain "newemail-add@example.com"
    And the page should contain "Unverified"
    And I take a screenshot named "settings_emails_added"

  Scenario: Add duplicate email shows error message
    Given I register and verify "emails-dup@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-dup@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    And I fill "input[name='email'][type='email']" with "emails-dup@example.com"
    And I click the "Add Email" button
    Then the page should contain "Email already registered"
    And I take a screenshot named "settings_emails_duplicate"

  Scenario: Unverified email shows verify and resend buttons
    Given I register and verify "emails-unv@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-unv@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    And I fill "input[name='email'][type='email']" with "newemail-unv@example.com"
    And I click the "Add Email" button
    Then the page should contain "newemail-unv@example.com"
    And the page should contain "Unverified"
    And the page should have an element "button:has-text('Verify')"
    And the page should have an element "button:has-text('Resend')"
    And the page should have an element "button:has-text('Remove')"
    And I take a screenshot named "settings_emails_unverified_buttons"

  Scenario: Remove a non-primary email shows success
    Given I register and verify "emails-rm@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "emails-rm@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/emails"
    And I fill "input[name='email'][type='email']" with "newemail-rm@example.com"
    And I click the "Add Email" button
    Then the page should contain "newemail-rm@example.com"
    When I click the "Remove" button
    Then the page should contain "Email removed"
    And I take a screenshot named "settings_emails_removed"
