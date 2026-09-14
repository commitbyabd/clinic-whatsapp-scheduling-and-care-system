import { Link } from "react-router-dom";
import Card from "./Card.jsx";
import IconBox from "./IconBox.jsx";

const ACTION_CLASS =
  "mt-6 inline-flex h-11 items-center rounded-md bg-(image:--gradient-primary-button) px-5 font-primary text-md font-semibold text-white shadow-button transition duration-200 hover:-translate-y-px focus-visible:ring-4 focus-visible:ring-violet/22 focus-visible:outline-none";

/*
  Full-page notice with a single way out. Used by the 404 and 403 pages.

  'action' is either { to, label } for navigation or { onClick, label } for
  something that has to run first, such as signing out.
*/
function MessageScreen({
  icon,
  iconClassName = "bg-lavender",
  title,
  message,
  action,
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-(image:--gradient-page) px-4 py-10">
      <Card className="w-full max-w-115 bg-porcelain/88 p-8 text-center shadow-card backdrop-blur-card">
        <div className="flex justify-center">
          <IconBox size="size-12" radius="rounded-lg" className={iconClassName}>
            {icon}
          </IconBox>
        </div>

        <h1 className="mt-5 font-primary text-heading-sm leading-heading font-semibold tracking-tight text-plum">
          {title}
        </h1>

        <p className="mt-2 font-primary text-md leading-body text-muted">
          {message}
        </p>

        {action?.to && (
          <Link to={action.to} className={ACTION_CLASS}>
            {action.label}
          </Link>
        )}

        {action?.onClick && (
          <button
            type="button"
            onClick={action.onClick}
            className={ACTION_CLASS}
          >
            {action.label}
          </button>
        )}
      </Card>
    </main>
  );
}

export default MessageScreen;
