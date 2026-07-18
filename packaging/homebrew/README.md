# Homebrew tap candidate

`Formula/macwise.rb` is the `1.0.0rc1` candidate for the future
`deesatzed/homebrew-tap` repository. Its main URL intentionally points to the GitHub
release source artifact that does not exist until publication. Every resource and SHA-256 is
derived from the locked macOS/Python 3.13 dependency closure.

Repository tests verify identity and lock alignment. Local `brew install` was not run
because it would alter the operator's shared Homebrew prefix and the main public artifact
is not published. After authority and publication, copy the formula into the tap, run
`brew audit --strict --online macwise`, install/test it in a clean hosted macOS runner,
and verify `brew install deesatzed/tap/macwise` from a fresh machine.
