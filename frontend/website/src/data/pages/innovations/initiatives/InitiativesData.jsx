/**
 * Four initiatives of equal weight. The AI booking feature is first but must
 * not dominate — card 02 is given the highest-contrast treatment (charcoal)
 * to balance it. If this list is reordered or restyled, preserve that
 * balance.
 */
export const initiativesData = [
  {
    id: "initiative-booking",
    index: "01",
    theme: "cream",
    status: { label: "Live", variant: "sage" },
    title: "Appointments that book themselves",
    description:
      "Message us in plain language — “knee hurts, can I come Thursday evening?” — and our AI assistant reads the department rota, holds a slot, and sends the confirmation. No forms, no hold music, no call-back window.",
    media: {
      type: "chat",
      label:
        "A booking conversation: the patient asks for a Thursday evening slot and the assistant confirms 5:40pm with Dr. Okafor.",
      messages: [
        {
          id: "booking-msg-1",
          from: "patient",
          text: "Knee's been bad a week. Thursday after 5?",
        },
        {
          id: "booking-msg-2",
          from: "assistant",
          text: "Dr. Okafor (Orthopedics) has 5:40pm Thursday. Booked — want the X-ray done first, same visit?",
        },
      ],
    },
    footnote:
      "Median time to a confirmed slot: 48 seconds · 71% of bookings now arrive this way",
  },
  {
    id: "initiative-research",
    index: "02",
    theme: "dark",
    status: { label: "Published", variant: "goldOnDark" },
    title: "Research our own doctors lead",
    description:
      "Dr. Anjali Rao's cardiology unit ran a four-year study on early rheumatic heart disease screening in school children. The protocol it produced is now used by 40+ district clinics and cut late-stage referrals by a third.",
    media: {
      type: "stats",
      items: [
        { id: "research-papers", value: "11", label: "peer-reviewed papers" },
        { id: "research-trials", value: "3", label: "active clinical trials" },
        {
          id: "research-clinics",
          value: "40+",
          label: "clinics using the protocol",
        },
      ],
    },
    footnote:
      "Every resident doctor gets four protected research hours a week.",
  },
  {
    id: "initiative-portal",
    index: "03",
    theme: "sand",
    status: { label: "Live", variant: "neutral" },
    title: "One patient record, yours to keep",
    description:
      "Scans, prescriptions, discharge notes and lab history in one portal — downloadable, shareable with any doctor outside Marigold, and written in language a patient can actually read.",
    media: {
      type: "records",
      hideOnMobile: true,
      rows: [
        {
          id: "record-blood",
          dot: "sage",
          label: "Blood panel — 12 Aug",
          state: "Normal",
          highlighted: true,
        },
        {
          id: "record-mri",
          dot: "gold",
          label: "Knee MRI — 4 Aug",
          state: "Review",
        },
        {
          id: "record-prescription",
          dot: "terracotta",
          label: "Prescription — refill due",
          state: "3 days",
        },
      ],
    },
    footnote:
      "18,400 patients enrolled · no charge, no advertising, no resale of data",
  },
  {
    id: "initiative-telemedicine",
    index: "04",
    theme: "cream",
    status: { label: "Expanding", variant: "rose" },
    title: "Telemedicine for the villages up the valley",
    description:
      "Six rural health posts now hold weekly video clinics with our specialists, with a trained health worker at the patient's end taking vitals live. Follow-ups that used to cost a day's travel take twenty minutes.",
    media: {
      type: "image",
      hideOnMobile: true,
      src: "/images/pages/innovations/telemedicine.avif",
      alt: "A health worker holding a tablet beside a patient during a video consult",
    },
    footnote:
      "6 posts live · 2 more opening this winter · 3,100 consults to date",
  },
];
