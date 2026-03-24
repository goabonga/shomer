# feat(tenant): Celery task for DNS verification + SSL provisioning

## Description

Scheduled Celery task that checks DNS records for pending custom domains and provisions SSL certificates via Certbot once DNS is verified.

## Objective

Automate the custom domain activation pipeline.

## Tasks

- [ ] Celery task: check DNS CNAME records for pending domains
- [ ] Update domain status on successful DNS verification
- [ ] Trigger Certbot SSL provisioning after DNS verification
- [ ] Update domain status on successful SSL provisioning
- [ ] Error handling and retry logic
- [ ] Status notifications (optional)
- [ ] Celery Beat schedule

## Dependencies

- #81 — custom domains

## Labels

`feature:tenant`, `type:infra`, `size:L`
