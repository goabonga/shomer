Feature: Advanced PAT management UI features

  Scenario: PAT create form shows expiration preset dropdown
    Given I register and verify "pat-adv-preset@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-preset@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    Then the page should have an element "select#expires-preset"
    And the page should contain "7 days"
    And the page should contain "30 days"
    And the page should contain "90 days"
    And the page should contain "1 year"
    And the page should contain "No expiration"
    And I take a screenshot named "pat_preset_dropdown"

  Scenario: Create PAT with expiration preset
    Given I register and verify "pat-adv-preset-create@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-preset-create@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "preset-key"
    And I select "30 days" from "select#expires-preset"
    And I click the "Create Token" button
    Then the page should contain "Token Created"
    And the page should contain "preset-key"
    And the page should contain "shm_pat_"
    And I take a screenshot named "pat_preset_created"

  Scenario: PAT table shows usage stats columns
    Given I register and verify "pat-adv-stats@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-stats@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "stats-key"
    And I click the "Create Token" button
    Then the page should contain "stats-key"
    And the page should contain "Uses"
    And the page should contain "Last IP"
    And I take a screenshot named "pat_usage_stats"

  Scenario: Regenerate button is shown for active tokens
    Given I register and verify "pat-adv-regen@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-regen@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "regen-key"
    And I click the "Create Token" button
    Then the page should contain "regen-key"
    And the page should contain "Regenerate"
    And I take a screenshot named "pat_regenerate_btn"

  Scenario: Regenerate PAT shows new token
    Given I register and verify "pat-adv-regen2@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-regen2@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "regen-key2"
    And I click the "Create Token" button
    Then the page should contain "Token Created"
    When I click the "Regenerate" button
    Then the page should contain "regenerated"
    And the page should contain "shm_pat_"
    And I take a screenshot named "pat_regenerated"

  Scenario: Revoke All button is shown when tokens exist
    Given I register and verify "pat-adv-rall@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-rall@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "rall-key"
    And I click the "Create Token" button
    Then the page should contain "rall-key"
    And the page should contain "Revoke All"
    And I take a screenshot named "pat_revoke_all_btn"

  Scenario: Revoke All revokes all tokens
    Given I register and verify "pat-adv-rall2@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "pat-adv-rall2@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/pats"
    And I fill "input[name='name']" with "rall2-a"
    And I click the "Create Token" button
    Then the page should contain "rall2-a"
    When I fill "input[name='name']" with "rall2-b"
    And I click the "Create Token" button
    Then the page should contain "rall2-b"
    When I click the "Revoke All" button
    Then the page should contain "All tokens revoked"
    And I take a screenshot named "pat_revoked_all"
