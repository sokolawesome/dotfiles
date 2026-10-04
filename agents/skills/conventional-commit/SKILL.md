---
name: conventional-commit
description: Prepare git commits with Conventional Commits messages. Use whenever the user asks to prepare, write, split or make commits from the current changes. Inspects the working tree, proposes one commit for a single logical change or several for unrelated changes, and waits for approval before committing.
---

# Conventional commit

## Workflow

1. Inspect the changes:

```bash
git status --short
git diff --stat HEAD
git diff HEAD
git log -n 10 --oneline
```

Read untracked files too, since `git diff` does not show them. Use the log to match existing scopes and message style.

2. Decide how many commits. Judge by logical concern, not by number of files or lines:
   - One commit per concern by default, several commits for unrelated changes.
   - If the user asks to batch unrelated changes into one commit anyway, the subject stays vague to cover them and a bullet body becomes mandatory.
   - If something is already staged, treat it as the user's intended first commit.

3. Order commits so the repo stays working after each one: refactors and dependencies before features, tests with or right after the code they cover.

4. Present the plan and stop. Do not stage or commit anything yet. Show the full message, including the body if there is one:

```
1. feat(hyprland): add scratchpad keybinds
   files: home/.config/hypr/binds.conf
2. chore(dotfiles): update fish and beets configs, add commit skill
   - update fish config file
   - add beets config
   - add conventional-commit skill
   files: home/.config/fish/config.fish, home/.config/beets/config.yaml, agents/skills/conventional-commit/SKILL.md
```

End with a short question: commit as proposed, or adjust?

5. After approval, for each commit in order:

```bash
git reset
git add <files>
git commit -m "<subject>" -m "<body>"
```

Skip `-m "<body>"` when there is no body. Finish with `git log --stat -n <count>` and show the result.

## Message format

```
type(scope): subject

- optional body line
- optional body line

optional footer
```

### Types

- feat: new feature or new capability
- fix: bug fix
- docs: documentation only
- style: formatting only, no behavior change (whitespace, indentation)
- refactor: code restructuring without changing behavior
- perf: performance improvement
- test: add or change tests
- build: build system or dependencies
- ci: CI configuration
- chore: maintenance that fits nowhere else (cleanup, renames, tooling)
- revert: revert a previous commit

If unsure between feat and chore for a config change: new functionality is feat, tweaking or tidying existing settings is chore, correcting broken behavior is fix.

### Scope

- Optional, lowercase, one word where possible.
- In a dotfiles repo, use the app or tool name: `hyprland`, `waybar`, `fish`, `nvim`, `stow`.
- In a code repo, use the module or package name.
- Reuse scopes already present in `git log`.
- Omit the scope when the change spans many areas.

### Subject

- Whole first line (`type(scope): subject`) is 50 characters or less.
- Imperative mood: "add", not "added" or "adds".
- Lowercase first letter, no trailing period.
- Specific: say what changed, not "update config" or "fix stuff".

### Body

Default is no body. Write the subject, stop.

A body is required in exactly one case: the commit bundles changes that do not share a reason, so the subject has to stay vague to cover all of them. `feat: some updates` followed by a bullet list is that shape. When the subject already names what changed, a body adds nothing.

Test before writing one: read the subject alone. Does a reader learn what changed from it? If yes, no body.

Format when a body is needed:

- bullet list, one change per line, each line starting with `- `
- lowercase, imperative, no trailing period, 72 characters or less per line
- never wrap a bullet onto a second line, shorten it instead
- no prose paragraphs, no explanations of why unless the user asks

### Footer

- Breaking changes: add `!` after the type or scope and a `BREAKING CHANGE:` footer.
- Issue references go in the footer.

### Examples

```
feat(hyprland): add scratchpad keybinds
fix(waybar): correct battery module icon
refactor(fish): split manage-df into helper functions
chore(nvim): remove unused plugins
docs: add stow usage to readme
style(alacritty): fix indentation in colors section
feat(api)!: drop support for v1 tokens
```

With a body:

```
chore(dotfiles): update fish and beets configs, add commit skill

- update fish config file
- add beets config
- add conventional-commit skill
```

## Rules

- Never commit before the user approves the plan.
- Never push, amend, rebase or use `--no-verify`.
- Never add co-author or generated-by trailers.
- No emojis in messages.
- If a commit hook fails, report the error and stop. Do not retry with different flags.
- Do not commit files that look like secrets or build artifacts. Flag them in the plan instead.
- If one file clearly contains changes for two different commits, keep it in the best fitting commit and mention it in the plan. Do not use `git add -p`.