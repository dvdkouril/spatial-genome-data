## Version control

We use jujutsu (jj-vcs) to track changes, with a git backend. A detached HEAD
and no current git branch are normal, so don't flag them. Use `jj` commands for
status, log, commits and bookmarks, not `git commit`/`git switch`.

It is preferred that you do not make commits or push to remotes, but instead
let the human inspect produced files, make commits, and push to remotes
themselves.
