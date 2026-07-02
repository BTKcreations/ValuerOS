Place your Rive animation file (.riv) here.

The StoryPlayer component expects a Rive file with a state machine named "StoryMachine"
containing the following inputs:

Trigger inputs (scene transitions):
  welcome, idle, thinking, success, warning, error,
  celebrate, walk, knock, document, handshake, exit

Trigger inputs (mood transitions):
  mood_neutral, mood_curious, mood_determined, mood_confident,
  mood_cautious, mood_focused, mood_happy, mood_satisfied

Number inputs (story variables):
  confidence (0-100), propertiesValued (0-N)

Boolean inputs (story variables):
  hasDocuments, reportReady

Without a .riv file, the StoryPlayer will show emoji-based fallback visuals
that still respond to Ink story tags and variables.