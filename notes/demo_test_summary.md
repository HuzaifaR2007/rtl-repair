# Demo Test Summary

The Gradio demo was tested with three preset examples:

1. Tick-driven FSM transition bug
2. 2-to-4 decoder missing default assignment
3. Modulo-6 counter terminal-count bug

## Result

All three presets produced correct RTL fixes.

## Notes

The edge-detector blocking-assignment example was removed from the preset list because the model produced a correct RTL fix but gave a weak explanation. It remains useful as a dataset/eval example, but it is not currently used as a judge-facing demo preset.

## Current Demo Presets

- Tick FSM bug: demonstrates targeted FSM failure recovery.
- Decoder missing default: demonstrates incomplete combinational logic repair.
- Modulo-6 counter: demonstrates off-by-one terminal count repair.