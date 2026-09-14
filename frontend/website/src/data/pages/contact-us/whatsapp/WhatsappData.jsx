import { PHONE_DISPLAY, WHATSAPP_HREF } from "../../../../utils/global/Constants";

export const whatsappData = {
  badge: "Answers 24/7",
  heading: "WhatsApp us",
  description:
    "You'll first reach our smart virtual assistant — it books, reschedules and sends reports in seconds. Ask for a team member whenever you'd rather talk to a person; during clinic hours that's under two minutes.",
  cta: { id: "whatsapp-cta", label: "Open WhatsApp chat", href: WHATSAPP_HREF },
  phone: PHONE_DISPLAY,
};

/* The page's key message: the assistant is a front door, not a wall. */
export const whatsappChat = {
  title: "Marigold Assistant",
  status: "online",
  label:
    "A WhatsApp conversation: the assistant offers to book, reschedule or send reports, the patient asks for a team member, and the assistant connects them to the front desk.",
  messages: [
    {
      id: "whatsapp-msg-1",
      from: "assistant",
      text: "Hi! I can book, reschedule or send your reports. What do you need?",
    },
    {
      id: "whatsapp-msg-2",
      from: "patient",
      text: "Can I speak to a team member?",
    },
    {
      id: "whatsapp-msg-3",
      from: "assistant",
      text: "Of course — connecting you to the front desk now.",
    },
  ],
};
