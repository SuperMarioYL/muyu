# vhs tape — CI-side regeneration path for the offline demo gif.
# The macOS-local fallback is docs/record_demo.py (same commands).
Output docs/assets/demo-muyu-score.gif
Set TypingSpeed 18ms
Set Width 1180
Set Height 740
Set FontSize 17
Set Padding 8
Type "muyu score examples/draft-1.md"
Enter
Sleep 2s
Type "muyu score examples/draft-2.md"
Enter
Sleep 2s
Type "muyu check examples/native-1.md --baseline 40"
Enter
Sleep 2s
Type "muyu presets"
Enter
Sleep 2s
