import { useEffect, useRef, useState, useCallback } from 'react';
import { Story } from 'inkjs';
import { useRive, useStateMachineInput, Layout, Fit, Alignment } from '@rive-app/canvas';

/**
 * Maps Ink story variables/tags to Rive state machine inputs.
 *
 * Architecture:
 *   Ink Story (JSON) ──tags──▶ Rive State Machine
 *   Ink variables ──numeric/boolean──▶ Rive SM inputs
 *
 * The Ink story drives the experience. Tags on story lines trigger
 * Rive animation states. Story variables map to Rive state machine
 * numeric/boolean inputs for smooth transitions.
 */

// ── Tag → Rive state mapping ──────────────────────────────────────────
// These tags appear in the Ink story and map to Rive state machine layers.
const TAG_TO_RIVE_STATE: Record<string, string> = {
  welcome: 'welcome',
  idle: 'idle',
  thinking: 'thinking',
  success: 'success',
  warning: 'warning',
  error: 'error',
  celebrate: 'celebrate',
  walk: 'walk',
  knock: 'knock',
  document: 'document',
  handshake: 'handshake',
  exit: 'exit',
};

// ── Ink variable → Rive number input mapping ──────────────────────────
const VARIABLE_TO_RIVE_NUMBER: Record<string, string> = {
  confidence: 'confidence',
  properties_valued: 'propertiesValued',
};

// ── Ink variable → Rive boolean input mapping ─────────────────────────
const VARIABLE_TO_RIVE_BOOLEAN: Record<string, string> = {
  has_documents: 'hasDocuments',
  report_ready: 'reportReady',
};

// ── Mood → Rive state mapping ─────────────────────────────────────────
const MOOD_TO_RIVE_STATE: Record<string, string> = {
  neutral: 'mood_neutral',
  curious: 'mood_curious',
  determined: 'mood_determined',
  confident: 'mood_confident',
  cautious: 'mood_cautious',
  focused: 'mood_focused',
  happy: 'mood_happy',
  satisfied: 'mood_satisfied',
};

interface StoryPlayerProps {
  /** URL path to the Ink story JSON file (e.g., "/stories/valuer-journey.ink.json") */
  storyUrl: string;
  /** URL path to the Rive animation file (.riv) */
  riveUrl: string;
  /** Rive artboard name to use (defaults to first artboard if omitted) */
  artboardName?: string;
  /** Rive state machine name to use (defaults to first SM if omitted) */
  stateMachineName?: string;
  /** Called when the story reaches END */
  onStoryEnd?: () => void;
  /** Called when story variables change */
  onVariablesChange?: (variables: Record<string, unknown>) => void;
  /** Custom class name for the container */
  className?: string;
}

export default function StoryPlayer({
  storyUrl,
  riveUrl,
  artboardName,
  stateMachineName,
  onStoryEnd,
  onVariablesChange,
  className = '',
}: StoryPlayerProps) {
  // ── Rive ───────────────────────────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null);
  const { rive, RiveComponent } = useRive({
    src: riveUrl,
    artboard: artboardName,
    stateMachines: stateMachineName || 'StoryMachine',
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
    autoplay: true,
  });

  // ── Ink ───────────────────────────────────────────────────────────
  const storyRef = useRef<Story | null>(null);
  const [storyText, setStoryText] = useState<string>('');
  const [currentTags, setCurrentTags] = useState<string[]>([]);
  const [choices, setChoices] = useState<{ index: number; text: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEnded, setIsEnded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Load Ink story ─────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    async function loadStory() {
      try {
        setIsLoading(true);
        const response = await fetch(storyUrl);
        if (!response.ok) throw new Error(`Failed to load story: ${response.status}`);
        const storyJson = await response.json();

        if (cancelled) return;

        const story = new Story(storyJson);
        storyRef.current = story;
        setIsLoading(false);

        // Start the story
        advanceStory();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load story');
          setIsLoading(false);
        }
      }
    }

    loadStory();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storyUrl]);

  // ── Advance the Ink story ──────────────────────────────────────────
  const advanceStory = useCallback(() => {
    const story = storyRef.current;
    if (!story || isEnded) return;

    let text = '';

    // Gather all text from continuation
    while (story.canContinue) {
      const line = story.Continue();
      text += (text ? '\n' : '') + line.trim();

      // Collect tags from this line
      const tags = story.currentTags ?? [];
      if (tags.length > 0) {
        setCurrentTags(tags);
      }
    }

    // Trim and set text
    const trimmed = text.trim();
    setStoryText(trimmed);

    // Check for choices
    const currentChoices = story.currentChoices.map((c) => ({
      index: c.index,
      text: c.text.trim(),
    }));
    setChoices(currentChoices);

    // Check if ended
    if (!story.canContinue && currentChoices.length === 0) {
      setIsEnded(true);
      onStoryEnd?.();
    }

    // Sync variables to Rive
    syncVariablesToRive(story);

    // Notify parent
    if (onVariablesChange) {
      const vars: Record<string, unknown> = {};
      for (const name of story.variablesState.$globalVariables.keys()) {
        vars[name] = story.variablesState.GetVariableWithName(name);
      }
      onVariablesChange(vars);
    }
  }, [isEnded, onStoryEnd, onVariablesChange]);

  // ── Sync Ink variables → Rive state machine inputs ─────────────────
  const syncVariablesToRive = useCallback(
    (story: Story) => {
      if (!rive) return;

      const inputs = rive.stateMachineInputs(stateMachineName || 'StoryMachine');
      if (!inputs || inputs.length === 0) return;

      for (const input of inputs) {
        // Number inputs
        const numMapping = VARIABLE_TO_RIVE_NUMBER[input.name];
        if (numMapping && input.type === 'number') {
          const val = story.variablesState.GetVariableWithName(numMapping);
          if (typeof val === 'number') {
            (input as { value: number }).value = val;
          }
        }

        // Boolean inputs
        const boolMapping = VARIABLE_TO_RIVE_BOOLEAN[input.name];
        if (boolMapping && input.type === 'boolean') {
          const val = story.variablesState.GetVariableWithName(boolMapping);
          if (typeof val === 'boolean') {
            (input as { value: boolean }).value = val;
          }
        }
      }
    },
    [rive, stateMachineName]
  );

  // ── Fire Rive state triggers based on Ink tags ─────────────────────
  useEffect(() => {
    if (!rive || currentTags.length === 0) return;

    const inputs = rive.stateMachineInputs(stateMachineName || 'StoryMachine');
    if (!inputs || inputs.length === 0) return;

    for (const tag of currentTags) {
      // Scene triggers
      const riveState = TAG_TO_RIVE_STATE[tag];
      if (riveState) {
        const trigger = inputs.find((i) => i.name === riveState);
        if (trigger && trigger.type === 'trigger') {
          (trigger as { fire: () => void }).fire();
        }
      }

      // Mood triggers
      const moodState = MOOD_TO_RIVE_STATE[tag];
      if (moodState) {
        const trigger = inputs.find((i) => i.name === moodState);
        if (trigger && trigger.type === 'trigger') {
          (trigger as { fire: () => void }).fire();
        }
      }
    }
  }, [rive, currentTags, stateMachineName]);

  // ── Handle choice selection ────────────────────────────────────────
  const handleChoice = useCallback(
    (choiceIndex: number) => {
      const story = storyRef.current;
      if (!story) return;

      story.ChooseChoiceIndex(choiceIndex);
      setChoices([]);
      setCurrentTags([]);
      advanceStory();
    },
    [advanceStory]
  );

  // ── Restart story ──────────────────────────────────────────────────
  const handleRestart = useCallback(() => {
    const story = storyRef.current;
    if (!story) return;

    // Reset Ink
    story.ResetState();

    // Reset Rive
    if (rive) {
      const inputs = rive.stateMachineInputs(stateMachineName || 'StoryMachine');
      if (inputs) {
        for (const input of inputs) {
          if (input.type === 'number') (input as { value: number }).value = 50;
          if (input.type === 'boolean') (input as { value: boolean }).value = false;
        }
      }
    }

    setIsEnded(false);
    setChoices([]);
    setCurrentTags([]);
    advanceStory();
  }, [rive, stateMachineName, advanceStory]);

  // ── Render ─────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 p-8 ${className}`}>
        <p className="text-sm font-medium text-destructive">Failed to load story</p>
        <p className="text-xs text-muted-foreground">{error}</p>
        <button
          onClick={() => {
            setError(null);
            setIsLoading(true);
            // Retry by forcing re-mount via key change handled by parent
            window.location.reload();
          }}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center rounded-xl border border-border bg-card p-8 ${className}`}>
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      {/* Rive Animation Canvas */}
      <div
        ref={containerRef}
        className="relative aspect-video w-full overflow-hidden rounded-xl border border-border bg-card shadow-sm"
        style={{ minHeight: 300 }}
      >
        <RiveComponent />
        {/* Fallback when no .riv file is available */}
        {!rive && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
            <div className="text-center">
              <div className="mb-2 text-4xl">
                {currentTags.includes('celebrate') && '🎉'}
                {currentTags.includes('thinking') && '🤔'}
                {currentTags.includes('success') && '✅'}
                {currentTags.includes('warning') && '⚠️'}
                {currentTags.includes('error') && '❌'}
                {currentTags.includes('document') && '📄'}
                {currentTags.includes('handshake') && '🤝'}
                {currentTags.includes('walk') && '🚶'}
                {currentTags.includes('knock') && '🚪'}
                {currentTags.includes('exit') && '👋'}
                {currentTags.length === 0 && '🏠'}
              </div>
              <p className="text-xs text-muted-foreground">
                {currentTags.length > 0
                  ? `Scene: ${currentTags.join(', ')}`
                  : 'Waiting for story...'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Story Text */}
      {storyText && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-primary">
            {storyText}
          </p>
        </div>
      )}

      {/* Choices */}
      {choices.length > 0 && !isEnded && (
        <div className="flex flex-wrap gap-3">
          {choices.map((choice) => (
            <button
              key={choice.index}
              onClick={() => handleChoice(choice.index)}
              className="rounded-lg border border-border bg-card px-5 py-3 text-sm font-medium text-primary shadow-sm transition-all hover:bg-accent hover:text-accent-foreground hover:shadow-md active:scale-[0.98]"
            >
              {choice.text}
            </button>
          ))}
        </div>
      )}

      {/* End State */}
      {isEnded && (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-8 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Story complete</p>
          <button
            onClick={handleRestart}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90 active:scale-[0.98]"
          >
            Play Again
          </button>
        </div>
      )}

      {/* Debug: Current Tags (hidden in production) */}
      {currentTags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {currentTags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-muted px-2.5 py-0.5 text-[10px] font-medium text-muted-foreground"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}