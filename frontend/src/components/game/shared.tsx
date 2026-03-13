// Barrel — re-exports all shared game components and hooks.
// Import from here for backward compatibility, or directly from the individual files.
export type { GameRound as Round, RoundResults, Props } from './types';
export type { GameRound } from './types';
export { useAudioPlayer, useAudioPlayerOnResults } from './useAudioPlayer';
export { AudioPlayerUI } from './AudioPlayerUI';
export { QuestionHeader } from './QuestionHeader';
export { OptionsGrid } from './OptionsGrid';
export { ResultFooter } from './ResultFooter';
export { TrackReveal } from './TrackReveal';
