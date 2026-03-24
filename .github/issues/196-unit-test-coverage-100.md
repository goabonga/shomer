# test(unit): achieve 100% unit test coverage

## Description

Current coverage is 93%. 16 files are below 100%. Add missing unit tests to reach full coverage.

## Tasks

### Routes (biggest gaps)

- [ ] routes/auth.py (61%) — lines 73-80, 110-115, 142-160, 198-235, 266-271, 305-312, 355-361, 400-419
- [ ] routes/oauth2.py (46%) — lines 107-112, 118-160, 503-544, 578-612

### Services

- [ ] services/auth_service.py (96%) — lines 437-448
- [ ] services/authorize_service.py (95%) — lines 170, 177, 193
- [ ] services/jwt_service.py (97%) — line 81
- [ ] services/jwt_validation_service.py (97%) — lines 166-167
- [ ] services/oauth2_client_service.py (95%) — lines 191, 201, 206, 228
- [ ] services/session_service.py (98%) — line 107
- [ ] services/token_service.py (93%) — lines 69-80, 477, 482

### Models / Core / Tasks

- [ ] deps.py (87%) — lines 43-45
- [ ] middleware/session.py (82%) — lines 46-48
- [ ] models/queries.py (88%) — lines 80-86
- [ ] models/user.py (94%) — line 88
- [ ] models/user_email.py (94%) — line 72
- [ ] models/user_password.py (93%) — line 56
- [ ] tasks/email.py (77%) — lines 57-59

## Labels

`type:test`
