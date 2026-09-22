# Admin portal

Status: built before the docs existed; written up 2026-09-22 · Area: backend + portal

## What it is

The admin's side of the staff portal, at `/dashboard`: adding, editing,
deactivating and restoring the doctors and receptionists who sign in to the
portal.

## What it does

A sidebar picks one of three lists, kept in the URL (`?tab=doctors`,
`receptionists` or `deactivated`):

- **Doctors** and **Receptionists:** cards with name, email and, for doctors,
  specialization; 8 per page. There are buttons to add, edit and deactivate.
- **Deactivated users:** both roles together, each with a Reactivate button.

**Add** asks for name, email and password, plus the specialization for a
doctor. The specialization is picked from a list of the chatbot's 12
departments (Dermatologist, Cardiologist, Pediatrician and so on). The new
account can sign in straight away. **Edit** changes the name, email and
specialization, but not the password. An old free-text specialization that
matches no department starts empty, showing "Choose a department (was
“Dermatology”)", so it has to be replaced. **Deactivate** and **Reactivate**
ask first. A deactivated account cannot sign in, but its record is kept.

The header across the portal reads "Marigold Health", with the portal's name
(Administrator, Reception or Doctor) beside it.

## How it works

Backend: `app/features/admin/route.py`, every route `require_role("admin")`:

| Endpoint | Does |
|---|---|
| `GET /admin/doctors`, `GET /admin/receptionists` | active accounts: id, name, email (and specialization) |
| `GET /admin/doctors/{id}`, `GET /admin/receptionists/{id}` | one account |
| `POST /admin/doctors`, `POST /admin/receptionists` | create; 409 `EMAIL_TAKEN` for a used email |
| `PATCH /admin/doctors/{id}`, `PATCH /admin/receptionists/{id}` | edit the fields sent |
| `PATCH …/{id}/deactivate`, `PATCH …/{id}/reactivate` | flip `is_active` |
| `GET /admin/deactivated-users` | inactive accounts of both roles |

The schemas are in `app/schemas/`: `doctor_create.py`, `doctor_update.py` and
`receptionist_*`. Passwords are hashed with bcrypt and emails stored in
lowercase. `known_specialization` in `doctor_create.py` checks a doctor's
specialization against `SPECIALIZATIONS` in `chatbot/classifier.py`.

Portal (`frontend/portal/src/`):

- `pages/dashboard/Dashboard.jsx` → `components/pages/dashboard/DashboardMain.jsx`
  (tab, list, dialogs, toast) → `ManagePanel.jsx` (the sidebar),
  `StaffCard.jsx`, `StaffFormModal.jsx` (add and edit), and the shared
  `ConfirmDialog`.
- `config/staffViews.js`: each list's wording and endpoints, in one place.
- `config/specializations.js`: the 12 departments, mirroring the chatbot's.
- `schemas/staff.js`: the form rules, mirroring the server's schemas.
- `api/admin.js`, `hooks/useStaffList.js`, `hooks/usePagination.js`.
- `components/pages/dashboard/ClinicIdentity.jsx`: the clinic name in the
  header.

## Decisions

- **Deactivate, never delete**, so appointment history keeps pointing at a
  doctor who still exists.
- **The specialization comes from the chatbot's own list.** When the model
  suggests "Dermatologist", reception gets the doctor filed under exactly
  that name pre-selected. Free text allowed "Dermatology", which never
  matched. The server enforces the list too.
- **The password is set only when the account is created.** There is no
  change-password endpoint, and an edit ignores the field.
- **The routes take their target from the URL**, unlike the doctor routes:
  an admin acts on other people's accounts.

## Tests

- `backend/tests/app/test_staff_schemas.py` (3): every department accepted,
  a name the chatbot does not use refused on create and edit, and an edit
  may leave the specialization out.
- `frontend/portal/src/schemas/staff.test.js`: the form rules, including
  departments only from the list.
- Checked on 2026-09-22 against a throwaway local database, not Atlas:
  - the header reads "Marigold Health";
  - Add shows the 12 departments;
  - an edit from Dermatologist to Pulmonologist saved;
  - an old "Dermatology" entry showed the prompt, was refused until a
    department was picked, then saved.

## How to try it

Sign in as an admin: you land on `/dashboard`.

## Next / known gaps

- There is no way to change or reset a password.
- Admins cannot set a doctor's working hours; doctors do that themselves,
  and `backend/scripts/seed_schedules.py` fills in a default week.
