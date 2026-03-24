## feat(ui): align profile settings page with all UserProfile editable fields

## Summary

- Expand the profile settings page to expose all 20+ UserProfile OIDC standard claims (identity, personal info, contact, picture, address) in collapsible sections
- Add POST handler in settings_ui.py for form submission (create/update UserProfile)
- Add missing fields (address, phone_number, profile_url, middle_name) to API ProfileUpdateRequest

## Changes

- [ ] Add POST /ui/settings/profile handler in settings_ui.py accepting all profile form fields
- [ ] Create or update UserProfile on form submission
- [ ] Display success/error messages after save
- [ ] Add address fields (street, locality, region, postal_code, country) and phone_number, profile_url, middle_name to API ProfileUpdateRequest
- [ ] Identity section (always visible): nickname, preferred_username, given_name, middle_name, family_name
- [ ] Personal Information section (collapsible): gender (dropdown), birthdate (date input), locale, zoneinfo
- [ ] Contact section (collapsible): phone_number, website, profile_url
- [ ] Picture URL section (collapsible): picture_url
- [ ] Address section (collapsible): address_street, address_locality, address_region, address_postal_code, address_country
- [ ] Show email as disabled field with note
- [ ] Show success/error flash messages
- [ ] Unit tests for POST /ui/settings/profile handler
- [ ] BDD happy path: profile page displays and saves all fields

## Dependencies

- #5 — UserProfile model
- #48 — UI user settings pages

## Related Issue

Closes #257

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
