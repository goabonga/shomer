## feat(tenant): Celery task for DNS verification + SSL provisioning

## Summary

Scheduled Celery task that checks DNS records for pending custom domains and provisions SSL certificates via Certbot once DNS is verified.

## Changes

- [ ] Celery task: check DNS CNAME records for pending domains
- [ ] Update domain status on successful DNS verification
- [ ] Trigger Certbot SSL provisioning after DNS verification
- [ ] Update domain status on successful SSL provisioning
- [ ] Error handling and retry logic
- [ ] Status notifications (optional)
- [ ] Celery Beat schedule

## Dependencies

- #81 - custom domains

## Related Issue

Closes #97

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


