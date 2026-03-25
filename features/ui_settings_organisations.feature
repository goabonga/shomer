Feature: Organisation settings UI pages

  Scenario: Organisations list redirects to login when unauthenticated
    When I open the page "/ui/settings/organisations"
    Then the page should contain "Login"
    And I take a screenshot named "settings_orgs_redirect"

  Scenario: Organisations list shows empty state when authenticated
    Given I register and verify "org-list@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-list@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations"
    Then the page should contain "Organisations"
    And the page should contain "Create Organisation"
    And I take a screenshot named "settings_orgs_empty"

  Scenario: Create organisation form renders correctly
    Given I register and verify "org-new@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-new@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    Then the page should contain "Create Organisation"
    And the page should have an element "input[name='slug']"
    And the page should have an element "input[name='name']"
    And the page should have an element "input[name='display_name']"
    And I take a screenshot named "settings_org_new_form"

  Scenario: Create organisation and view detail page
    Given I register and verify "org-create@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-create@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "test-org-bdd"
    And I fill "input[name='name']" with "Test Org BDD"
    And I fill "input[name='display_name']" with "Test Organisation BDD"
    And I click the "Create" button
    Then the page should contain "Test Organisation BDD"
    And the page should contain "General"
    And the page should contain "Members"
    And the page should contain "Roles"
    And the page should contain "Identity Providers"
    And the page should contain "Branding"
    And the page should contain "Trust Policies"
    And the page should contain "Domains"
    And the page should contain "Templates"
    And I take a screenshot named "settings_org_detail"

  Scenario: Edit organisation details
    Given I register and verify "org-edit@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-edit@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "edit-org-bdd"
    And I fill "input[name='name']" with "Edit Org"
    And I fill "input[name='display_name']" with "Edit Organisation"
    And I click the "Create" button
    Then the page should contain "Edit Organisation"
    When I fill "input[name='display_name']" with "Updated Organisation"
    And I click the "Save" button
    Then the page should contain "updated successfully"
    And I take a screenshot named "settings_org_edited"

  Scenario: Members page shows current user as owner
    Given I register and verify "org-mem@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-mem@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "mem-org-bdd"
    And I fill "input[name='name']" with "Mem Org"
    And I fill "input[name='display_name']" with "Member Org"
    And I click the "Create" button
    Then the page should contain "Member Org"
    When I click the "Members" link
    Then the page should contain "Members"
    And the page should contain "owner"
    And I take a screenshot named "settings_org_members"

  Scenario: Roles page shows empty state and create form
    Given I register and verify "org-roles@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-roles@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "roles-org-bdd"
    And I fill "input[name='name']" with "Roles Org"
    And I fill "input[name='display_name']" with "Roles Org"
    And I click the "Create" button
    Then the page should contain "Roles Org"
    When I click the "Roles" link
    Then the page should contain "Roles"
    And the page should contain "Create Role"
    And the page should contain "No custom roles defined yet"
    And I take a screenshot named "settings_org_roles_empty"

  Scenario: Create a custom role
    Given I register and verify "org-role-c@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-role-c@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "rolec-org-bdd"
    And I fill "input[name='name']" with "RoleC Org"
    And I fill "input[name='display_name']" with "RoleC Org"
    And I click the "Create" button
    Then the page should contain "RoleC Org"
    When I click the "Roles" link
    Then the page should contain "Create Role"
    When I fill "input[name='role_name']" with "editor"
    And I fill "input[name='permissions']" with "read write"
    And I click the "Create" button
    Then the page should contain "created"
    And the page should contain "editor"
    And I take a screenshot named "settings_org_role_created"

  Scenario: Identity providers page shows empty state
    Given I register and verify "org-idp@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-idp@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "idp-org-bdd"
    And I fill "input[name='name']" with "IdP Org"
    And I fill "input[name='display_name']" with "IdP Org"
    And I click the "Create" button
    Then the page should contain "IdP Org"
    When I click the "Identity Providers" link
    Then the page should contain "Identity Providers"
    And the page should contain "Add Identity Provider"
    And the page should contain "No identity providers configured yet"
    And I take a screenshot named "settings_org_idps_empty"

  Scenario: Branding page shows customization form
    Given I register and verify "org-brand@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-brand@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "brand-org-bdd"
    And I fill "input[name='name']" with "Brand Org"
    And I fill "input[name='display_name']" with "Brand Org"
    And I click the "Create" button
    Then the page should contain "Brand Org"
    When I click the "Branding" link
    Then the page should contain "Branding"
    And the page should have an element "input[name='logo_url']"
    And the page should have an element "input[name='primary_color']"
    And the page should have an element "input[name='font_family']"
    And the page should contain "Save Branding"
    And I take a screenshot named "settings_org_branding"

  Scenario: Save branding settings
    Given I register and verify "org-brand-s@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-brand-s@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "brands-org-bdd"
    And I fill "input[name='name']" with "BrandS Org"
    And I fill "input[name='display_name']" with "BrandS Org"
    And I click the "Create" button
    Then the page should contain "BrandS Org"
    When I click the "Branding" link
    And I fill "input[name='primary_color']" with "#333333"
    And I fill "input[name='font_family']" with "Inter, sans-serif"
    And I click the "Save Branding" button
    Then the page should contain "updated successfully"
    And I take a screenshot named "settings_org_branding_saved"

  Scenario: Trust policies page shows trust mode and empty sources
    Given I register and verify "org-trust@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-trust@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "trust-org-bdd"
    And I fill "input[name='name']" with "Trust Org"
    And I fill "input[name='display_name']" with "Trust Org"
    And I click the "Create" button
    Then the page should contain "Trust Org"
    When I click the "Trust Policies" link
    Then the page should contain "Trust Policies"
    And the page should contain "Trust Mode"
    And the page should contain "No trusted sources configured"
    And I take a screenshot named "settings_org_trust"

  Scenario: Domains page shows custom domain form
    Given I register and verify "org-dom@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-dom@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "dom-org-bdd"
    And I fill "input[name='name']" with "Dom Org"
    And I fill "input[name='display_name']" with "Dom Org"
    And I click the "Create" button
    Then the page should contain "Dom Org"
    When I click the "Domains" link
    Then the page should contain "Custom Domain"
    And the page should have an element "input[name='custom_domain']"
    And I take a screenshot named "settings_org_domains"

  Scenario: Templates page shows empty state and create form
    Given I register and verify "org-tmpl@example.com" with password "securepassword123"
    When I open the page "/ui/login"
    And I fill "input[name='email']" with "org-tmpl@example.com"
    And I fill "input[name='password']" with "securepassword123"
    And I click the "Login" button
    Then the page URL should contain "/"
    When I navigate to "/ui/settings/organisations/new"
    And I fill "input[name='slug']" with "tmpl-org-bdd"
    And I fill "input[name='name']" with "Tmpl Org"
    And I fill "input[name='display_name']" with "Tmpl Org"
    And I click the "Create" button
    Then the page should contain "Tmpl Org"
    When I click the "Templates" link
    Then the page should contain "Email Templates"
    And the page should contain "Create Template Override"
    And the page should contain "No custom template overrides configured"
    And I take a screenshot named "settings_org_templates_empty"
