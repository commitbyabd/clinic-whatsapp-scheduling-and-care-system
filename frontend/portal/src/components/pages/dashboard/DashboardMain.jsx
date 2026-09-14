import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus } from "lucide-react";
import DashboardHeader from "./DashboardHeader.jsx";
import ManagePanel from "./ManagePanel.jsx";
import SectionHeader from "./SectionHeader.jsx";
import StaffCard from "./StaffCard.jsx";
import StaffFormModal from "./StaffFormModal.jsx";
import ConfirmDialog from "../../ui/ConfirmDialog.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Toast from "../../ui/Toast.jsx";
import Pagination from "../../ui/Pagination.jsx";
import { readApiError } from "../../../api/auth.js";
import { DEFAULT_VIEW_SLUG, findView } from "../../../config/staffViews.js";
import { useStaffList } from "../../../hooks/useStaffList.js";
import { usePagination } from "../../../hooks/usePagination.js";
import { initialsFrom } from "../../../utils/initials.js";

const PAGE_SIZE = 8;

function DashboardMain() {
  // The tab lives in the URL, so a refresh keeps it and a colleague can be
  // sent straight to the list being discussed.
  const [searchParams, setSearchParams] = useSearchParams();
  const slug = searchParams.get("tab") ?? DEFAULT_VIEW_SLUG;
  const view = findView(slug);

  const { status, items, message, refresh } = useStaffList(view);
  const {
    page,
    pageCount,
    total,
    pageItems,
    rangeStart,
    rangeEnd,
    setPage,
    reset,
  } = usePagination(items, PAGE_SIZE);

  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [confirming, setConfirming] = useState(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [confirmError, setConfirmError] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  // Counter rather than a timestamp: two toasts raised in the same
  // millisecond would share a key and the second would inherit the first
  // one's remaining timer.
  const toastId = useRef(0);
  const [toast, setToast] = useState(null);
  const showToast = (text) => {
    toastId.current += 1;
    setToast({ id: toastId.current, text });
  };

  const selectView = (nextSlug) => {
    setSearchParams({ tab: nextSlug }, { replace: true });
    // Both belong to the list they were made in.
    setSelectedId(null);
    reset();
  };

  const closeConfirm = () => {
    setConfirming(null);
    setConfirmError("");
  };

  // A view either takes access away or gives it back, never both, so one
  // handler covers the dialog for every list.
  const isRestore = Boolean(view?.reactivate);

  const handleConfirm = async () => {
    setConfirmBusy(true);
    setConfirmError("");

    // Captured before the dialog closes, since confirming is null by the
    // time the toast is shown.
    const target = confirming;

    try {
      // Reactivate takes the whole row: the endpoint depends on the role,
      // which only the row knows in a mixed list.
      await (isRestore ? view.reactivate(target) : view.deactivate(target.id));

      setConfirming(null);
      showToast(
        `${target.full_name} was ${isRestore ? "reactivated" : "deactivated"} successfully.`,
      );
      refresh();
    } catch (error) {
      setConfirmError(readApiError(error));
    } finally {
      setConfirmBusy(false);
    }
  };

  const isList = Boolean(view?.fetchList);
  // Only the role-specific lists can create: 'Add deactivated user' is not
  // a thing an admin would ask for.
  const canCreate = Boolean(view?.kind);
  const count =
    status === "loading"
      ? "Loading…"
      : `${total} record${total === 1 ? "" : "s"}`;

  return (
    <div className="relative min-h-screen bg-porcelain">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-(image:--gradient-page) opacity-40"
      />

      <div className="relative">
        <DashboardHeader />

        <div className="mx-auto grid max-w-310 grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[300px_minmax(0,1fr)]">
          <ManagePanel activeSlug={view?.slug} onSelect={selectView} />

          <section className="min-w-0">
            <SectionHeader
              title={view?.title ?? "Not found"}
              subtitle={view?.subtitle ?? ""}
              count={isList ? count : ""}
              action={
                canCreate && (
                  <Button
                    variant="primary"
                    leadingIcon={
                      <Plus className="size-4.5" strokeWidth={2.25} />
                    }
                    onClick={() => setCreating(true)}
                  >
                    Add {view.noun}
                  </Button>
                )
              }
            />

            <div className="mt-5 space-y-4">
              {isList && status === "error" && <Alert>{message}</Alert>}

              {isList && status === "loading" && (
                <p className="font-primary text-sm text-muted">
                  Loading {view.noun}s…
                </p>
              )}

              {isList && status === "ready" && total === 0 && (
                <p className="font-primary text-sm text-muted">{view.empty}</p>
              )}

              {isList && status === "ready" && total > 0 && (
                <>
                  {/* API field names are mapped here so StaffCard stays
                      presentation and never sees the backend's vocabulary */}
                  <div
                    role="listbox"
                    aria-label={view.title}
                    className="space-y-4"
                  >
                    {pageItems.map((member) => (
                      <StaffCard
                        key={member.id}
                        initials={initialsFrom(member.full_name)}
                        name={member.full_name}
                        specialty={member.specialization}
                        // The deactivated list mixes roles, so its rows
                        // carry their own.
                        role={member.role ?? view.role}
                        email={member.email}
                        selected={member.id === selectedId}
                        onSelect={() =>
                          setSelectedId((current) =>
                            current === member.id ? null : member.id,
                          )
                        }
                        onEdit={
                          isRestore ? undefined : () => setEditing(member)
                        }
                        onDeactivate={
                          isRestore ? undefined : () => setConfirming(member)
                        }
                        onReactivate={
                          isRestore ? () => setConfirming(member) : undefined
                        }
                      />
                    ))}
                  </div>

                  <Pagination
                    page={page}
                    pageCount={pageCount}
                    total={total}
                    rangeStart={rangeStart}
                    rangeEnd={rangeEnd}
                    onChange={setPage}
                  />
                </>
              )}
            </div>
          </section>
        </div>
      </div>

      {creating && isList && (
        <StaffFormModal
          kind={view.kind}
          onClose={() => setCreating(false)}
          onSaved={(text) => {
            setCreating(false);
            showToast(text || `The ${view.noun} was added successfully.`);
            refresh();
          }}
        />
      )}

      {editing && isList && (
        <StaffFormModal
          staff={editing}
          kind={view.kind}
          onClose={() => setEditing(null)}
          onSaved={(text, saved) => {
            setEditing(null);
            // The name just typed, not the one the list still holds.
            showToast(`${saved.full_name}'s fields updated successfully.`);
            refresh();
          }}
        />
      )}

      {confirming && isList && (
        <ConfirmDialog
          title={isRestore ? "Reactivate account" : `Deactivate ${view.noun}`}
          message={
            isRestore
              ? `Restore access for ${confirming.full_name}? They will be able to sign in again straight away.`
              : `Are you sure you want to deactivate ${confirming.full_name}? They lose access immediately, but the record is kept and can be reactivated later.`
          }
          confirmLabel={isRestore ? "Reactivate" : "Deactivate"}
          confirmVariant={isRestore ? "primary" : "danger"}
          busy={confirmBusy}
          error={confirmError}
          onConfirm={handleConfirm}
          onClose={closeConfirm}
        />
      )}

      {toast && (
        <Toast
          key={toast.id}
          message={toast.text}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default DashboardMain;
