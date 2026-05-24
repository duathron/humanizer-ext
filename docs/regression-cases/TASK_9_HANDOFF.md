# Task 9 Handoff: Manual Regression for v3.3.0 Phase 0 Refactor

Copy everything between the `===` lines below into a **fresh Claude Code session** (new conversation, not the one that did the refactor). The fresh session must have the humanizer-ext fork installed as a skill — either via plugin install, or by symlinking the worktree SKILL.md to your `~/.claude/skills/humanizer/SKILL.md`.

---

## Pre-flight (one-time setup in your shell, NOT inside Claude)

```bash
# Verify the refactored SKILL.md is what your Claude Code session will load
ls -l ~/.claude/skills/humanizer/SKILL.md  # check what's installed

# If your installed version is still v3.2.0 (monolithic ~60KB), point it at the worktree:
ln -sfn "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext/.claude/worktrees/v3.3.0-refactor/SKILL.md" \
  ~/.claude/skills/humanizer/SKILL.md

# Also symlink the pack files alongside so the framework can Read them
mkdir -p ~/.claude/skills/humanizer/patterns ~/.claude/skills/humanizer/domains
ln -sfn "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext/.claude/worktrees/v3.3.0-refactor/patterns/_universal.md" \
  ~/.claude/skills/humanizer/patterns/_universal.md
ln -sfn "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext/.claude/worktrees/v3.3.0-refactor/patterns/en.md" \
  ~/.claude/skills/humanizer/patterns/en.md
ln -sfn "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext/.claude/worktrees/v3.3.0-refactor/domains/en_overrides.md" \
  ~/.claude/skills/humanizer/domains/en_overrides.md

# Sanity: SKILL.md size should now be ~15KB (was ~60KB)
wc -c ~/.claude/skills/humanizer/SKILL.md
```

After symlinks: start a **NEW** Claude Code session so the skill gets re-discovered. Then paste the prompt below.

---

## Paste this into the fresh Claude Code session

===

I need to run a manual regression test for the humanizer-ext skill (v3.3.0 Phase 0 refactor). The skill was just split from a monolithic SKILL.md into a framework + pattern packs. This test verifies the refactor produces equivalent output for English input.

**Your job:**

1. Invoke the `humanizer` skill in Full mode (default) against the input below.
2. Output both Draft and Final rewrite.
3. After you finish, I will compare your output to a pre-refactor baseline.

**Important:** Do NOT skim, do NOT abbreviate. Run the full skill pipeline including:
- Language detection (should be `en`)
- Reading `patterns/_universal.md`, `patterns/en.md`, `domains/en_overrides.md`
- Domain detection
- Tier-1 density preflight
- Length audit
- Final 13-point AI audit
- Both Draft and Final outputs as specified in the skill's Output Format

Announce the detected domain and the density preflight result before the draft.

---

**Input to humanize:**

> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - 💡 **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - 🚀 **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - ✅ **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies—including hallucinations, bias, and accountability—the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you'd like me to expand on any section!

---

Run `/humanizer` on the input above. Produce Draft and Final.

===

---

## After the fresh session produces output

Copy the fresh session's full output (domain announcement + density preflight + Draft + Final + audit findings) and **paste it back to me in the original refactor session**. I will:

1. Compare against the v3.2.0 baseline stored in `docs/regression-cases/full_example.md`.
2. Score it against the pass criteria:
   - Removes chatbot artifacts ("Great question!", "I hope this helps!", "Let me know if...")
   - Removes significance inflation ("testament", "pivotal moment", "evolving landscape")
   - Removes promotional language ("groundbreaking", "nestled", "seamless")
   - Removes em dashes and emojis
   - Removes copula avoidance ("serves as", "functions as", "stands as")
   - Removes formulaic challenges section
   - Removes generic positive conclusion
   - Output length within ~20% of baseline (~250–400 words for the final)
3. Write `docs/regression-cases/RESULTS.md` with PASS or FAIL + analysis.
4. If PASS → proceed to Task 10 (gitignore + README + version bump + tag v3.3.0).
5. If FAIL → iterate on the framework SKILL.md until the regression closes.

---

## Cleanup after PASS

```bash
# Remove the symlinks if you don't want the worktree to stay active in your global skill install
rm ~/.claude/skills/humanizer/SKILL.md ~/.claude/skills/humanizer/patterns/_universal.md ~/.claude/skills/humanizer/patterns/en.md ~/.claude/skills/humanizer/domains/en_overrides.md
# Reinstall via plugin marketplace once v3.3.0 ships:
# /plugin install humanizer-ext@duathron-skills
```

---

## Alternative if symlinks are too fiddly

Skip the symlinks and run the regression entirely inline by pasting the contents of the refactored SKILL.md + the three pack files as system context into the fresh Claude Code session, then asking it to apply the skill manually. This is less true to how Claude Code loads skills but a reasonable approximation if the symlink path is too painful.
