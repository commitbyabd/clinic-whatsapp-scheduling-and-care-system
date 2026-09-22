# Staff passwords

Status: built 2026-09-22 · Area: backend + portal

## What it is

How staff passwords change after an account is created. Anyone signed in
can change their own, and an admin can reset a doctor's or receptionist's.
Either one signs out every session that used the old password.

## What it does

- **Change password.** The key icon in the portal header, next to sign out,
  on every portal. It asks for the current password, then the new one
  twice. The current session carries on; any other device signed in to the
  account is signed out.
- **Reset password.** On each card in the admin's doctor and receptionist
  lists. It sets a new password, which the admin passes on, because there
  is no email to send a reset link. Anyone signed in as that person is
  signed out.
- **Deactivating an account** now shuts it out at once. Before, a token
  already issued kept working for up to an hour.

## How it works

- `POST /auth/change-password`, for any signed-in user
  (`app/features/auth/v1/change_password.py`). Body `{current_password,
  new_password}`. It returns a fresh `access_token` in the envelope, which
  the portal swaps in.
  - 400 `WRONG_PASSWORD`: the current password is wrong. It is a 400, not
    a 401, so a mistyped password does not sign the user out.
  - 400 `SAME_PASSWORD`: the new password matches the old one.
- `PUT /admin/staff/{user_id}/password`, admin only
  (`app/features/admin/v1/reset_staff_password.py`). Body `{new_password}`.
  Doctors and receptionists only; any other account is 404.
- Both save a bcrypt hash and `password_changed_at`
  (`password_changed_now()` in `app/core/security.py`, in whole seconds).
- Tokens now carry `iat`. `get_current_user` in `app/dependencies/auth.py`
  refuses, on every request:
  - an account that is not active;
  - a token issued before `password_changed_at`.

  A token from before this change carries no `iat`, and expires within the
  hour anyway.
- Schemas: `app/schemas/password_update.py`. New passwords are 8 to 64
  characters, like a new account's.

Portal:

- `components/pages/dashboard/ChangePasswordModal.jsx`, opened from
  `HeaderUser.jsx`. On success it calls `signIn` with the new token.
- `ResetPasswordModal.jsx`, opened from a new button in `StaffActions.jsx`.
- `schemas/password.js`: the rules, plus the second copy of the new
  password, which never leaves the browser.
- `api/auth.js` has `changePassword`; `api/admin.js` has
  `resetStaffPassword`.
- `Modal` and `Toast` render into `document.body` now. The header's blur
  would otherwise trap a dialog opened from it inside the header bar.

## Decisions

- **The current password is asked for again**, so an unattended open
  session cannot be used to take the account over.
- **Other sessions end** on a change or a reset. That is the point of a
  reset after a lost or shared password.
- **Admins reset, rather than users resetting by email**, since the clinic
  has no email sending.

## Tests

- `backend/tests/app/test_passwords.py` (11), with real bcrypt:
  - changing your password keeps you signed in on a fresh token;
  - a wrong or unchanged password is refused, and the limits apply;
  - an admin resets staff, but not another admin;
  - an old session ends after a change, a newer one carries on, and a
    deactivated account is refused at once;
  - both routes need a signed-in user.
- `frontend/portal/src/schemas/password.test.js`: the two copies must
  match, the new password must differ, and the length limits.
- Checked in the portal on 2026-09-22:
  - both dialogs open over the whole page;
  - an empty submit shows its messages.

  No password was typed during these checks.

## How to try it

Sign in and press the key icon in the header. As an admin, press "Reset
password" on a doctor's card.

## Next / known gaps

- There is no self-service reset by email.
- An admin's own password is changed only through the header, never by
  another admin.
