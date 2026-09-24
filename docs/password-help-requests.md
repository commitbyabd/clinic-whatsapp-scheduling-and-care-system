# Forgot your password

Status: built 2026-09-24 · Area: backend + portal

## What it is

A staff member who cannot sign in sends their email from the sign-in page.
It reaches the admin as a note in a **Password requests** tab, and the admin
resets the password with the button that was already there
([staff-passwords.md](staff-passwords.md)) and tells them the new one.

## The question it had to answer

*What stops someone resetting a colleague's password?* Nothing about this
form resets anything. It only leaves a note, and only an admin can act on
it, so typing someone else's email achieves nothing. There is no reset link
to steal, no token to guess and no mail to intercept.

The usual email-a-link design was not built: it needs SMTP credentials the
project does not have, and the clinic already has an admin who resets
passwords by hand.

## What it does

On the sign-in page, under the form, "Forgot your password?" opens a small
box with one email field. Sending it always answers the same way:

> Thanks. If that email belongs to a staff account, our admin team will
> reset the password and get in touch.

The same sentence comes back whether the address is a doctor's, a
stranger's or nonsense, so the form cannot be used to find out who has an
account. Nothing about the account goes back in the response.

A note is only kept for an account an admin can actually reset: an active
doctor or receptionist. An unknown address, a deactivated account or an
admin's own email leaves nothing behind, and the sender is told the same
either way.

In the admin portal, **Password requests** lists who is waiting, newest
first: their name, role, email, when they asked and how many times. The
list reloads every 30 seconds. Each row has:

- **Reset password** — the same dialog as the staff lists. Doing it closes
  the request, whichever tab the admin resets from.
- **Dismiss** — takes the row off the list and changes no password. The
  person can ask again.

Asking again while a request is open bumps its count instead of adding a
row, so ten taps on Send are still one line for the admin. Asking after one
was handled starts a fresh row.

## How it works

Backend:

| Endpoint | File | Who |
|---|---|---|
| `POST /auth/password-help` | `features/auth/v1/request_password_help.py` | nobody signed in — whoever needs it cannot sign in |
| `GET /admin/password-requests` | `features/admin/v1/get_password_requests.py` | admin |
| `PATCH /admin/password-requests/{id}/done` | `features/admin/v1/close_password_request.py` | admin |

- The body is `{email}` (`app/schemas/password_help.py`), checked as an
  email address, so a typo is a 422 before anything is stored.
- `find_staff_query` looks for an active doctor or receptionist with that
  address; `record_request_query` upserts one open request per person,
  `$inc`s `times_asked` and stores a snapshot of their name, email and role.
- `close_requests_for_user` runs after `reset_staff_password`, so the reset
  answers the request by itself. If that write fails the reset still
  succeeds; only the list is left stale.
- Document in `password_requests`: `user_id, email, full_name, role, status
  (new | handled), times_asked, asked_at, created_at, handled_by,
  handled_at`. See [database.md](database.md).
- Indexes (`app/core/indexes.py`): `(status, asked_at desc)` for the list,
  and a unique `user_id` where `status` is `new`
  (`one_open_password_request_per_user`).

Portal:

- `components/pages/login/ForgotPasswordBox.jsx`, closed until it is asked
  for, so the page has one email field until then. The confirmation shown is
  the server's own message.
- `config/staffViews.js` gains the `requests` view; `DashboardMain.jsx`
  draws `PasswordRequestCard.jsx` for it instead of `StaffCard`.
- `api/auth.js: requestPasswordHelp`, `api/admin.js: listPasswordRequests`
  and `closePasswordRequest`, `schemas/password.js: passwordHelpSchema`.

## Decisions

- **No email, no link, no token.** An admin was already the reset path, so
  the request is a message rather than a credential. Nothing sent can be
  stolen, and the project needs no SMTP account.
- **The same reply every time.** "No account with that email" would turn the
  form into a way of listing staff.
- **Only accounts an admin can reset leave a note.** A request nobody can
  act on is worse than none: it sits in the list looking like work.
- **The email never reaches the logs.** It identifies a person, and an
  address typed by mistake could be a patient's.
- **One open request per person**, so pressing Send repeatedly cannot fill
  the admin's screen.
- **Dismiss changes no password.** It is for a request already sorted out by
  phone, or one sent by mistake.

## Tests

- `backend/tests/app/test_password_requests.py` (18): a staff email leaves a
  note, an unknown one leaves nothing and reads the same, the address is
  matched however it is typed, admin and deactivated accounts leave nothing,
  asking again bumps the count, a new ask after a handled one starts a row,
  a database fault says so without details, the email never reaches the
  logs, the form needs no token and refuses a bad address, the list holds
  only what the admin needs and only what is waiting, newest first,
  dismissing, a 404 for one already done, a 400 for a bad id, a reset
  answers the request, and a reset still works when the request cannot be
  closed.
- `frontend/portal/src/schemas/password.test.js`: the box sends the email
  and nothing else, and catches a typo.
- Checked on 2026-09-24 against a throwaway local database, not Atlas:
  - the box on the sign-in page sent a doctor's address and showed the
    confirmation; a stranger's address showed the same sentence and left
    nothing in the database;
  - asking twice left one row reading "asked 2 times";
  - the admin's Password requests tab listed both waiting staff with their
    name, role, email and time;
  - Dismiss took a row off the list, and resetting a password closed that
    person's request on its own.

## How to try it

On the sign-in page, open "Forgot your password?", send a staff email, then
sign in as the admin and open **Password requests**. Reset from the row and
watch it leave the list.

## Next / known gaps

- **An admin who forgets their own password cannot be helped from the
  portal.** Nothing resets an admin there, so their request is not even
  recorded. It needs a script on the server.
- The person is told nothing automatically; the admin passes the new
  password on themselves, as before.
- The endpoint is public and not rate limited. One open row per person caps
  what it can do to the admin's screen, but a flood of requests still
  reaches the database.
