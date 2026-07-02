import { useState } from 'react';
import StoryPlayer from '@/components/ink-rive/StoryPlayer';

/**
 * Demo page showcasing Ink + Rive integration.
 *
 * This page demonstrates the "show, don't tell" approach:
 * - Ink story drives the narrative flow and choices
 * - Rive animations visualize the story state (scenes, moods, transitions)
 * - Story variables (confidence, properties_valued, etc.) map to Rive state machine inputs
 *
 * To use with a real .riv file:
 * 1. Design your Rive animation with a state machine named "StoryMachine"
 * 2. Add trigger inputs matching TAG_TO_RIVE_STATE keys (welcome, idle, thinking, etc.)
 * 3. Add number inputs matching VARIABLE_TO_RIVE_NUMBER keys (confidence, propertiesValued)
 * 4. Add boolean inputs matching VARIABLE_TO_RIVE_BOOLEAN keys (hasDocuments, reportReady)
 * 5. Place the .riv file in public/animations/ and update riveUrl below
 */

// ── Demo story variables display ──────────────────────────────────────
function VariablesPanel({ variables }: { variables: Record<string, unknown> }) {
  const entries = Object.entries(variables);
  if (entries.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Story State
      </h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {entries.map(([key, value]) => (
          <div
            key={key}
            className="rounded-lg bg-muted/50 px-3 py-2"
          >
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {key}
            </p>
            <p className="mt-0.5 text-sm font-semibold text-primary">
              {typeof value === 'boolean' ? (value ? '✓ Yes' : '✗ No') : String(value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RiveInkDemoPage() {
  const [variables, setVariables] = useState<Record<string, unknown>>({});
  const [playCount, setPlayCount] = useState(0);

  const handleStoryEnd = () => {
    // Could trigger confetti, analytics, etc.
  };

  const handleRestart = () => {
    setPlayCount((c) => c + 1);
    setVariables({});
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-primary">
          Ink + Rive Integration Demo
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          "Show, don't tell" — The Ink story drives Rive animations.
          Story variables and tags control visual states.
        </p>
      </div>

      {/* Story Player */}
      <StoryPlayer
        key={playCount}
        storyUrl="/stories/valuer-journey.ink.json"
        riveUrl="/animations/valuer-animation.riv"
        stateMachineName="StoryMachine"
        onStoryEnd={handleStoryEnd}
        onVariablesChange={setVariables}
        className="w-full"
      />

      {/* Variables Panel */}
      <VariablesPanel variables={variables} />

      {/* Integration Guide */}
      <details className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-primary">
          How It Works
        </summary>
        <div className="mt-4 space-y-3 text-xs leading-relaxed text-muted-foreground">
          <p>
            <strong className="text-primary">1. Ink Story (.ink.json)</strong> — Defines the narrative
            flow with choices, variables, and tags. Tags like <code>#thinking</code>,{' '}
            <code>#success</code>, <code>#celebrate</code> trigger Rive animation states.
          </p>
          <p>
            <strong className="text-primary">2. Rive Animation (.riv)</strong> — Contains a state
            machine with trigger inputs matching the tag names. When Ink emits a tag,
            the corresponding Rive trigger fires, transitioning the animation.
          </p>
          <p>
            <strong className="text-primary">3. Variable Mapping</strong> — Ink variables like{' '}
            <code>confidence</code> (0-100) and <code>has_documents</code> (bool) map to
            Rive number/boolean inputs for smooth, data-driven animations.
          </p>
          <p>
            <strong className="text-primary">4. StoryPlayer Component</strong> — Bridges Ink and
            Rive: loads the story, advances on user choices, syncs variables to Rive
            inputs, and fires triggers based on story tags.
          </p>
        </div>
      </details>

      {/* Setup Instructions */}
      <div className="rounded-xl border border-border bg-muted/30 p-6">
        <h3 className="mb-3 text-sm font-semibold text-primary">
          To use with your own Rive file:
        </h3>
        <ol className="list-inside list-decimal space-y-1.5 text-xs text-muted-foreground">
          <li>Design your animation in Rive and add a state machine named <code>StoryMachine</code></li>
          <li>Add trigger inputs: <code>welcome</code>, <code>idle</code>, <code>thinking</code>, <code>success</code>, <code>warning</code>, <code>error</code>, <code>celebrate</code>, <code>walk</code>, <code>knock</code>, <code>document</code>, <code>handshake</code>, <code>exit</code></li>
          <li>Add mood triggers: <code>mood_neutral</code>, <code>mood_curious</code>, <code>mood_determined</code>, <code>mood_confident</code>, <code>mood_cautious</code>, <code>mood_focused</code>, <code>mood_happy</code>, <code>mood_satisfied</code></li>
          <li>Add number inputs: <code>confidence</code> (0-100), <code>propertiesValued</code> (0-N)</li>
          <li>Add boolean inputs: <code>hasDocuments</code>, <code>reportReady</code></li>
          <li>Export as <code>.riv</code> and place in <code>public/animations/</code></li>
          <li>Update <code>riveUrl</code> prop on StoryPlayer</li>
        </ol>
      </div>
    </div>
  );
}