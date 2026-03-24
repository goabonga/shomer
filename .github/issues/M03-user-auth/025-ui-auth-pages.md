# feat(auth): [UI] registration, verification and login pages

## Description

Jinja2/HTMX pages for registration (form + ToS), email verification (code input), and login (email/password + post-login redirect).

## Objective

Provide the browser-facing auth UI for all user-facing authentication flows.

## Tasks

- [ ] Registration page with form validation
- [ ] Email verification page with code input and resend button
- [ ] Login page with redirect support (`next` parameter)
- [ ] Shared layout / base template
- [ ] Error and success state display

## Dependencies

- #17 — registration API
- #18 — verification API
- #19 — login API

## Labels

`feature:auth`, `layer:ui`, `size:L`
