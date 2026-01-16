import type { Plugin } from "@opencode-ai/plugin"

export const SayNotificationPlugin: Plugin = async ({ app, client, $ }) => {
  console.log("Say Notification Plugin initialized!")

  return {
    event: async ({ event }) => {
      // Trigger when session becomes idle (user stops interacting)
      if (event.type === "session.idle") {
        try {
          await $`notify-send "Your opencode session is now idle and ready for new input"`
        } catch (error) {
          console.error("Failed to use say command:", error)
        }
      }
    },
  }
}
