---
title: Kodiak decision model
emoji: 🐻
colorFrom: gray
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: apache-2.0
short_description: Typed questions in, calibrated answers out, one pass
---

Demo of **Kodiak** by Cortex Agent LLC: an open-weights, encoder-only decision model. Give it a state and typed questions;
it answers all of them in one forward pass with calibrated probabilities, and abstains when the state doesn't contain the answer.
Code and docs: https://github.com/grizzlypeaksoftware/kodiak
