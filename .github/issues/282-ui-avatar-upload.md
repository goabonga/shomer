# feat(ui): avatar upload on profile settings page

## Description

Add avatar/profile picture upload to the profile settings page. Support file upload (JPEG, PNG, GIF, WebP, max 5MB) with preview. Store as URL in UserProfile.picture_url.

## Objective

Allow users to upload and manage their profile avatar directly from the settings page.

## Tasks

- [ ] File upload form on profile page
- [ ] POST /ui/settings/profile/avatar handler
- [ ] Image validation (type, size)
- [ ] Store uploaded file and update picture_url
- [ ] Display current avatar with fallback
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #257 — UI profile settings all fields

## Labels

`feature:ui`, `layer:ui`, `size:S`
