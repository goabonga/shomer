# feat(ui): align profile settings page with all UserProfile editable fields

## Description

The profile settings page (`/ui/settings/profile`) only exposes **4 fields** (name, nickname, locale, zoneinfo) while the `UserProfile` model has **20+ editable fields** matching OIDC standard claims. The equivalent page in the `auth/` project exposes all fields with collapsible sections. This issue brings Shomer's profile page to feature parity.

Additionally, the UI form submits via `POST` but `settings_ui.py` has **no POST handler** — only a GET. A POST handler must be added for the form to actually save data.

## Objective

Expose all UserProfile fields on the profile settings page, organized in collapsible sections, with a working POST handler for form submission.

## Tasks

### Backend — POST handler for profile form

- [ ] Add POST /ui/settings/profile handler in settings_ui.py accepting all profile form fields
- [ ] Create or update UserProfile on form submission
- [ ] Display success/error messages after save
- [ ] Add address fields (street, locality, region, postal_code, country) and phone_number, profile_url, middle_name to API ProfileUpdateRequest

### Template — complete profile form

- [ ] Identity section (always visible): nickname, preferred_username, given_name, middle_name, family_name
- [ ] Personal Information section (collapsible): gender (dropdown), birthdate (date input), locale, zoneinfo
- [ ] Contact section (collapsible): phone_number, website, profile_url
- [ ] Picture URL section (collapsible): picture_url
- [ ] Address section (collapsible): address_street, address_locality, address_region, address_postal_code, address_country
- [ ] Show email as disabled field with note
- [ ] Show success/error flash messages

### Tests

- [ ] Unit tests for POST /ui/settings/profile handler
- [ ] BDD happy path: profile page displays and saves all fields

## Dependencies

- #5 — UserProfile model
- #48 — UI user settings pages

## Labels

`feature:ui`, `type:route`, `layer:ui`, `size:M`
