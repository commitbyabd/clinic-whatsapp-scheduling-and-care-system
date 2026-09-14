function LoginHeading() {
  return (
    <div>
      <h1 className="font-primary text-heading-sm leading-heading font-semibold tracking-tight text-plum sm:text-heading">
        Good to see you
      </h1>
      {/* The max-width is what wraps the description onto two lines */}
      <p className="mt-2 max-w-[36ch] font-primary text-md leading-body text-muted">
        Enter your assigned credentials to open the clinic dashboard.
      </p>
    </div>
  );
}

export default LoginHeading;
