# SpecAnvil demo GIF — regenerate with:  vhs scripts/demo.tape
# Requires: brew install vhs   (run from repo root)
Output docs/assets/demo.gif

Set FontSize 15
Set Width 1180
Set Height 640
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Padding 16

Type "# 一份「假详细」PRD：支持智能搜索、体验要好 → 上门禁"
Enter
Sleep 800ms
Type "specanvil check examples/case-order-cancel-bad/machine/spec.yaml"
Enter
Sleep 3200ms
Type "clear"
Enter
Type "# 修成可开发规格（状态矩阵 + 文案原文 + 可观察 AC）→ 再上门禁"
Enter
Sleep 800ms
Type "specanvil check examples/case-order-cancel-bad/machine/spec.fixed.yaml"
Enter
Sleep 2800ms
Type "# RESULT: PASS — 零 LLM，确定性判定，可挂 CI"
Enter
Sleep 2000ms
