# Evaluation Version Matrix

Every compatibility result stores this exact tuple:

- macOS product version and build;
- Darwin version;
- architecture;
- Python and relevant system-tool versions.

`validated_live` requires a private real-Mac reference comparison on that exact tuple.
`validated_replay` requires replay of a frozen capsule. `provisional`, `unsupported`, and `unknown`
must remain visibly conservative; no result inherits status merely because the macOS marketing name
or major version is similar.

Hosted macOS jobs record their exact runtime tuple as an artifact. They supplement local evidence;
they do not substitute for the user’s private Mac or imply support for an untested future build.
