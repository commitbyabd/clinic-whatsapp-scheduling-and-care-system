import { useState } from "react";
import { Copy, Plus, X } from "lucide-react";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Card from "../../ui/Card.jsx";
import SelectField from "../../ui/SelectField.jsx";
import SmallField from "../../ui/SmallField.jsx";
import { saveSchedule } from "../../../api/doctor.js";
import { readApiError } from "../../../api/auth.js";
import { formatDay } from "../../../utils/appointments.js";
import { todayInClinic } from "../../../utils/scheduling.js";
import {
  DAYS,
  SLOT_CHOICES,
  formatClock,
  weekErrors,
  weekFromSchedule,
  weekPayload,
  weeklyHours,
} from "../../../utils/workingHours.js";

// what "Add hours" fills in: a morning block first, then an evening one
const SUGGESTED = [
  { start: "09:00", end: "13:00" },
  { start: "17:00", end: "20:00" },
];

const hoursLabel = (hours) => `${hours} hour${hours === 1 ? "" : "s"}`;

function HoursEditor({ initial, onSaved }) {
  const [week, setWeek] = useState(() => weekFromSchedule(initial));
  // what was last saved, to tell whether anything has changed since
  const [baseline, setBaseline] = useState(() =>
    JSON.stringify(weekPayload(weekFromSchedule(initial))),
  );
  const [today] = useState(todayInClinic);
  const [newDayOff, setNewDayOff] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // worked out on every change, so a clash shows as it is typed
  const errors = weekErrors(week);
  const tone = submitted ? "error" : "hint";
  const changed = JSON.stringify(weekPayload(week)) !== baseline;

  const changeDays = (change) =>
    setWeek((current) => ({ ...current, days: change(current.days) }));

  const setBlock = (day, index, field, value) =>
    changeDays((days) =>
      days.map((blocks, d) =>
        d !== day
          ? blocks
          : blocks.map((block, i) =>
              i === index ? { ...block, [field]: value } : block,
            ),
      ),
    );

  const addBlock = (day) =>
    changeDays((days) =>
      days.map((blocks, d) =>
        d !== day
          ? blocks
          : [...blocks, { ...(SUGGESTED[blocks.length] ?? { start: "", end: "" }) }],
      ),
    );

  const removeBlock = (day, index) =>
    changeDays((days) =>
      days.map((blocks, d) =>
        d !== day ? blocks : blocks.filter((_, i) => i !== index),
      ),
    );

  // most doctors keep the same hours most days: set one, copy, then clear
  // the days off
  const copyToEveryDay = (day) =>
    changeDays((days) => days.map(() => days[day].map((block) => ({ ...block }))));

  const addDayOff = () => {
    if (newDayOff && !week.daysOff.includes(newDayOff)) {
      setWeek((current) => ({
        ...current,
        daysOff: [...current.daysOff, newDayOff].sort(),
      }));
    }
    setNewDayOff("");
  };

  const removeDayOff = (day) =>
    setWeek((current) => ({
      ...current,
      daysOff: current.daysOff.filter((d) => d !== day),
    }));

  const save = async () => {
    setSubmitted(true);
    setFormError("");
    if (Object.keys(errors).length > 0) return;

    const payload = weekPayload(week);
    setSaving(true);
    try {
      const envelope = await saveSchedule(payload);
      setBaseline(JSON.stringify(payload));
      setSubmitted(false);
      onSaved(envelope.data);
    } catch (error) {
      setFormError(readApiError(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <SectionHeader
        title="Working hours"
        subtitle="Reception books your visits into these times, in clinic time"
        count={`${hoursLabel(weeklyHours(week))} a week`}
      />

      <Card className="mt-5 bg-porcelain/92 p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-6">
        <fieldset disabled={saving}>
          <SelectField
            id="hours-slot"
            label="Length of one visit"
            className="sm:max-w-xs"
            value={week.slotMinutes}
            onChange={(event) =>
              setWeek((current) => ({
                ...current,
                slotMinutes: event.target.value,
              }))
            }
          >
            {SLOT_CHOICES.map((minutes) => (
              <option key={minutes} value={String(minutes)}>
                {minutes} minutes
              </option>
            ))}
          </SelectField>
          <p className="mt-2 font-primary text-sm text-muted">
            Visits already booked keep their time.
          </p>

          <ul className="mt-6 border-t border-border">
            {week.days.map((blocks, day) => (
              <li
                key={DAYS[day]}
                className="grid gap-3 border-b border-border py-4 sm:grid-cols-[9rem_minmax(0,1fr)]"
              >
                <div>
                  <p className="font-primary text-md font-semibold text-plum">
                    {DAYS[day]}
                  </p>
                  <p className="font-primary text-xs text-muted">
                    {blocks.length === 0 ? "Day off" : `${blocks.length} block${blocks.length === 1 ? "" : "s"}`}
                  </p>
                </div>

                <div className="space-y-3">
                  {blocks.map((block, index) => {
                    const error = errors[`${day}.${index}`];
                    const id = `hours-${day}-${index}`;
                    return (
                      <div key={index}>
                        <div className="flex flex-wrap items-end gap-2">
                          <SmallField
                            id={`${id}-start`}
                            label="From"
                            type="time"
                            step={300}
                            className="w-36"
                            value={block.start}
                            onChange={(event) =>
                              setBlock(day, index, "start", event.target.value)
                            }
                          />
                          <SmallField
                            id={`${id}-end`}
                            label="To"
                            type="time"
                            step={300}
                            className="w-36"
                            value={block.end}
                            onChange={(event) =>
                              setBlock(day, index, "end", event.target.value)
                            }
                          />
                          <button
                            type="button"
                            onClick={() => removeBlock(day, index)}
                            aria-label={`Remove ${DAYS[day]} ${
                              block.start && block.end
                                ? `${formatClock(block.start)} to ${formatClock(block.end)}`
                                : "hours"
                            }`}
                            className="grid size-10 place-items-center rounded-md text-muted transition duration-200 hover:bg-error-bg hover:text-error focus-visible:ring-2 focus-visible:ring-error/30 focus-visible:outline-none"
                          >
                            <X className="size-4" strokeWidth={2} />
                          </button>
                        </div>
                        {error && (
                          <p
                            role={tone === "error" ? "alert" : "status"}
                            className={`mt-1 font-primary text-xs ${tone === "error" ? "text-error" : "text-hint"}`}
                          >
                            {error}
                          </p>
                        )}
                      </div>
                    );
                  })}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => addBlock(day)}
                      leadingIcon={<Plus className="size-4" strokeWidth={2} />}
                    >
                      Add hours
                    </Button>
                    {blocks.length > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToEveryDay(day)}
                        leadingIcon={<Copy className="size-4" strokeWidth={2} />}
                      >
                        Copy to every day
                      </Button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-6">
            <h2 className="font-primary text-md font-semibold text-plum">
              Days off
            </h2>
            <p className="mt-1 font-primary text-sm text-muted">
              No visits are offered on these dates, even on a working day.
            </p>

            <div className="mt-3 flex flex-wrap items-end gap-2">
              <SmallField
                id="hours-day-off"
                label="Date"
                type="date"
                min={today}
                className="w-44"
                value={newDayOff}
                onChange={(event) => setNewDayOff(event.target.value)}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={addDayOff}
                disabled={!newDayOff}
                className="h-10 disabled:pointer-events-none disabled:opacity-60"
              >
                Add day off
              </Button>
            </div>

            {week.daysOff.length > 0 && (
              <ul className="mt-3 flex flex-wrap gap-2">
                {week.daysOff.map((day) => (
                  <li
                    key={day}
                    className="inline-flex items-center gap-1 rounded-pill bg-lavender py-1 pr-1 pl-3 font-primary text-sm text-plum"
                  >
                    {formatDay(day)}
                    <button
                      type="button"
                      onClick={() => removeDayOff(day)}
                      aria-label={`Remove the day off on ${formatDay(day)}`}
                      className="grid size-6 place-items-center rounded-pill text-muted transition duration-200 hover:bg-white hover:text-plum focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none"
                    >
                      <X className="size-3.5" strokeWidth={2} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </fieldset>

        {errors.total && <Alert className="mt-6">{errors.total}</Alert>}
        {formError && <Alert className="mt-6">{formError}</Alert>}

        <div className="mt-6 flex flex-wrap items-center justify-end gap-3 border-t border-border pt-5">
          {changed && (
            <p className="font-primary text-sm text-muted">Unsaved changes</p>
          )}
          <Button
            variant="primary"
            onClick={save}
            disabled={saving || !changed}
            className="disabled:pointer-events-none disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save working hours"}
          </Button>
        </div>
      </Card>
    </>
  );
}

/*
  The doctor's weekly hours and days off. DoctorMain loads the schedule,
  since the appointments tab needs to know whether any hours are set too.
*/
function WorkingHoursView({ schedule, onSaved }) {
  if (schedule.status === "loading") {
    return (
      <p className="font-primary text-sm text-muted">
        Loading your working hours…
      </p>
    );
  }

  if (schedule.status === "error") return <Alert>{schedule.message}</Alert>;

  return <HoursEditor initial={schedule.data} onSaved={onSaved} />;
}

export default WorkingHoursView;
