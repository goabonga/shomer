# feat(federation): [UI] provider selection and callback

## Description

Jinja2/HTMX UI for social login: provider selection buttons on the login page, callback handling page (loading state while processing).

## Objective

Provide the browser UI for initiating and completing social login flows.

## Tasks

- [ ] Social login buttons on login page (Google, GitHub, etc.)
- [ ] Provider-specific icons and styling
- [ ] Redirect to IdP authorization URL on click
- [ ] Callback landing page (processing state)
- [ ] Error display for failed federation

## Dependencies

- #85 — federation providers API
- #86 — federation callback

## Labels

`feature:federation`, `layer:ui`, `size:M`
