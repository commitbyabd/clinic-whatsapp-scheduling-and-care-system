export const pricingIntro = {
  eyebrow: "No surprises",
  heading: "What it costs, published before you come in.",
  description:
    "Flat prices for the things people ask about most. If a procedure will exceed its estimate, you hear it from us before it happens — not on the bill.",
};

/* Card 4 is the hinge of the section: the price list earns the trust, and
   the charcoal $0 card converts it into the Fund story directly below.
   Do not restyle it to match the others, move it, or drop it on mobile. */
export const pricingData = [
  {
    id: "price-consultation",
    title: "Consultation",
    price: "$40",
    note: "Any specialty. Follow-up within 14 days is free.",
  },
  {
    id: "price-blood-panel",
    title: "Full blood panel",
    price: "$55",
    note: "Results the same evening, in your portal.",
  },
  {
    id: "price-mri",
    title: "MRI, single region",
    price: "$310",
    note: "Includes the radiologist's report, not billed separately.",
  },
  {
    id: "price-fund",
    title: "Can't pay?",
    price: "$0",
    note: "Everything above, free through the Marigold Fund. Ask at the desk.",
    emphasis: true,
  },
];
