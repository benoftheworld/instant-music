/**
 * Sound effects manager for game UX.
 * 
 * Uses the Web Audio API to generate synthesized sounds,
 * so no external audio files are needed.
 */

class SoundEffectsManager {
  private audioContext: AudioContext | null = null;
  private enabled: boolean = true;
  private volume: number = 0.5;

  private getContext(): AudioContext {
    if (!this.audioContext || this.audioContext.state === 'closed') {
      this.audioContext = new AudioContext();
    }
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
    return this.audioContext;
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  setVolume(volume: number) {
    this.volume = Math.max(0, Math.min(1, volume));
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  getVolume(): number {
    return this.volume;
  }

  /**
   * Play a synthesized tone.
   */
  private playTone(
    frequency: number,
    duration: number,
    type: OscillatorType = 'sine',
    rampDown = true,
  ) {
    if (!this.enabled) return;
    try {
      const ctx = this.getContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(frequency, ctx.currentTime);
      gain.gain.setValueAtTime(this.volume * 0.3, ctx.currentTime);

      if (rampDown) {
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      }

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + duration);
    } catch {
      // Silently fail if audio context is unavailable
    }
  }

  /**
   * Play a sequence of tones.
   */
  private playSequence(
    notes: { freq: number; dur: number; delay: number; type?: OscillatorType }[],
  ) {
    if (!this.enabled) return;
    try {
      const ctx = this.getContext();
      for (const note of notes) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = note.type || 'sine';
        osc.frequency.setValueAtTime(note.freq, ctx.currentTime + note.delay);
        gain.gain.setValueAtTime(this.volume * 0.25, ctx.currentTime + note.delay);
        gain.gain.exponentialRampToValueAtTime(
          0.001,
          ctx.currentTime + note.delay + note.dur,
        );

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + note.delay);
        osc.stop(ctx.currentTime + note.delay + note.dur);
      }
    } catch {
      // Silently fail
    }
  }

  // ─── Game event sounds ─────────────────────────────────────────

  /** Correct answer – happy ascending arpeggio */
  correctAnswer() {
    this.playSequence([
      { freq: 523, dur: 0.15, delay: 0 },       // C5
      { freq: 659, dur: 0.15, delay: 0.1 },      // E5
      { freq: 784, dur: 0.3, delay: 0.2 },       // G5
    ]);
  }

  /** Wrong answer – descending low tone */
  wrongAnswer() {
    this.playSequence([
      { freq: 311, dur: 0.2, delay: 0, type: 'triangle' },  // Eb4
      { freq: 233, dur: 0.4, delay: 0.15, type: 'triangle' }, // Bb3
    ]);
  }

  /** Timer tick – soft click for last 5 seconds */
  timerTick() {
    this.playTone(800, 0.05, 'square');
  }

  /** Timer warning – urgent beep for last 3 seconds */
  timerWarning() {
    this.playTone(1000, 0.1, 'square');
  }

  /** Time's up – buzzer sound */
  timeUp() {
    this.playSequence([
      { freq: 440, dur: 0.3, delay: 0, type: 'sawtooth' },
      { freq: 350, dur: 0.5, delay: 0.25, type: 'sawtooth' },
    ]);
  }

  /** Round start / countdown beep */
  countdownBeep() {
    this.playTone(660, 0.12, 'sine');
  }

  /** Round start – final GO beep (higher pitch) */
  countdownGo() {
    this.playTone(880, 0.25, 'sine');
  }

  /** Player joined lobby */
  playerJoined() {
    this.playSequence([
      { freq: 440, dur: 0.1, delay: 0 },
      { freq: 554, dur: 0.15, delay: 0.08 },
    ]);
  }

  /** Game started – triumphant fanfare */
  gameStarted() {
    this.playSequence([
      { freq: 523, dur: 0.15, delay: 0 },        // C5
      { freq: 523, dur: 0.15, delay: 0.15 },      // C5
      { freq: 523, dur: 0.15, delay: 0.3 },       // C5
      { freq: 784, dur: 0.5, delay: 0.5 },        // G5
    ]);
  }

  /** Game finished – victory jingle */
  gameFinished() {
    this.playSequence([
      { freq: 523, dur: 0.2, delay: 0 },          // C5
      { freq: 659, dur: 0.2, delay: 0.15 },       // E5
      { freq: 784, dur: 0.2, delay: 0.3 },        // G5
      { freq: 1047, dur: 0.6, delay: 0.5 },       // C6
    ]);
  }

  /** Button click / answer selection */
  click() {
    this.playTone(600, 0.04, 'sine');
  }

  /** Answer submitted (sent to server) */
  answerSubmitted() {
    this.playTone(500, 0.08, 'triangle');
  }

  /** New round loading */
  roundLoading() {
    this.playSequence([
      { freq: 350, dur: 0.15, delay: 0, type: 'triangle' },
      { freq: 440, dur: 0.2, delay: 0.12, type: 'triangle' },
    ]);
  }
}

/** Singleton instance */
export const soundEffects = new SoundEffectsManager();
