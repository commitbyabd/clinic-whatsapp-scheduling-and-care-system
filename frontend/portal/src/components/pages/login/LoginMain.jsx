import LoginHeading from "./LoginHeading.jsx";
import LoginForm from "./LoginForm.jsx";
import SecurityNote from "./SecurityNote.jsx";

/*
  Layout only. Every visual piece lives in its own file; this arranges them
  and owns the spacing between them.

  Vertical rhythm per spec:
    description -> form   32px (mt-8)
    button -> security    28px (mt-7)
*/
function LoginMain() {
  return (
    <main className="grid min-h-screen place-items-center bg-(image:--gradient-page) px-4 py-10 sm:px-6">
      <section className="w-full max-w-(--login-card-width) rounded-xl border border-white/75 bg-porcelain/88 p-6 shadow-card backdrop-blur-card sm:p-10">
        <LoginHeading />

        <div className="mt-8">
          <LoginForm />
        </div>

        <div className="mt-7">
          <SecurityNote />
        </div>
      </section>
    </main>
  );
}

export default LoginMain;
