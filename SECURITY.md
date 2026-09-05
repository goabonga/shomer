# Security Policy

Shomer is an authorization server. A defect here is an authentication or
authorization defect for everything that trusts it, so reports are taken
seriously and handled privately by default.

## Supported versions

Each package in this workspace is versioned and released on its own. Fixes
land on `main` and ship in the next release of the affected package; older
releases are not patched.

| Version | Supported |
| --- | --- |
| latest release of a package | ✅ |
| older releases | ❌ |

## Reporting a vulnerability

**Please do not open a public issue.** GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
is the preferred channel:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Describe the issue with reproduction steps and a suggested mitigation.

If you cannot use GitHub's form, email **goabonga@pm.me** with the same
information. PGP encryption is available on request.

You can expect an acknowledgement within **3 business days**, a triage
assessment within **10 business days**, and a fix or written mitigation
plan before any public disclosure.

## Scope

The parts most relevant to security are the ones that decide who someone
is and what they may do: token issuance and validation, session handling,
redirect-URI and client validation, and anything reachable without
authentication. The browser-facing surface (`packages/web`, rendered by
`packages/ssr`) counts too — it renders values the server hands it.

Vulnerabilities in third-party dependencies should be reported upstream,
but please tell us as well so the pinned ranges can be bumped.

Thanks for helping keep the project and its users safe.
