# intent-drift terminal demo
# Uses VHS (https://github.com/charmbracelet/vhs)
Set FontSize 16
Set Width 1100
Set Height 600
Set Padding 12
Set Margin 20
Set Theme "Dracula"
Set TypingSpeed 25ms
Set Framerate 30

Output "/Users/shwetag/Projects/intent-drift-skill/docs/media/intent-drift-demo.gif"

Type "export PS1='intent-drift> ' PROMPT='intent-drift> ' RPROMPT=''" Enter
Sleep 700ms
Type "source .venv/bin/activate" Enter
Sleep 900ms
Type "cd ~/Projects/intent-drift-skill" Enter
Sleep 700ms
Type "clear" Enter
Sleep 400ms

Type "intent-drift --help" Enter
Sleep 1.5s

Type "clear" Enter
Sleep 400ms

Type "intent-drift --original-goal 'Reduce the runtime memory usage of the app' --current-plan 'Optimize the startup initialization path' --auto-context --format markdown" Enter
Sleep 5s

Type "clear" Enter
Sleep 400ms

Type "intent-drift --original-goal 'Add CSV export to the report generator' --current-plan 'Refactor the export layer into a plugin system' --auto-context" Enter
Sleep 5s

Type "clear" Enter
Sleep 400ms

Type "intent-drift --history" Enter
Sleep 1.5s

Type "clear" Enter
Sleep 400ms

Type "intent-drift --original-goal 'Add CSV export to the report generator' --current-plan 'Refactor the export layer into a plugin system' --compare 1" Enter
Sleep 4s
