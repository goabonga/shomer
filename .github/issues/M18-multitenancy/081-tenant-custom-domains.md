# feat(tenant): custom domains (CNAME, Nginx, SSL Certbot)

## Description

Custom domain support for tenants: CNAME verification, Nginx vhost configuration generation, SSL certificate provisioning via Certbot/Let's Encrypt.

## Objective

Allow tenants to use their own domain for the auth server.

## Tasks

- [ ] CNAME/DNS verification service
- [ ] Nginx vhost config generation per tenant domain
- [ ] SSL certificate provisioning via Certbot
- [ ] Certificate renewal tracking
- [ ] Domain status tracking (pending_dns, pending_ssl, active, error)
- [ ] Admin API for domain management
- [ ] Integration tests (DNS verification)

## Dependencies

- #79 — Tenant model
- #80 — tenant resolver middleware

## Labels

`feature:tenant`, `size:XL`
