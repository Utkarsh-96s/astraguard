/**
 * ASTRA-GUARD Voice Announcer (Q5).
 *
 * Uses the Web Speech API (window.speechSynthesis) to speak
 * synthesized mission safety advisories and critical alert warnings.
 */

class VoiceAnnouncer {
  private isEnabled: boolean = true;

  constructor() {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("astra_voice_enabled");
      this.isEnabled = saved !== "false";
    }
  }

  public toggle(): boolean {
    this.isEnabled = !this.isEnabled;
    if (typeof window !== "undefined") {
      localStorage.setItem("astra_voice_enabled", String(this.isEnabled));
    }
    if (this.isEnabled) {
      this.announce("Voice announcer online. Mission Safety channel active.");
    }
    return this.isEnabled;
  }

  public getEnabled(): boolean {
    return this.isEnabled;
  }

  public announce(text: string): void {
    if (!this.isEnabled) return;
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    try {
      window.speechSynthesis.cancel(); // Stop prior queue
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 0.95;

      // Select an English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha"))
      ) || voices.find((v) => v.lang.startsWith("en"));

      if (preferred) {
        utterance.voice = preferred;
      }

      window.speechSynthesis.speak(utterance);
    } catch {
      // SpeechSynthesis policy suppression
    }
  }
}

export const voiceAnnouncer = new VoiceAnnouncer();
