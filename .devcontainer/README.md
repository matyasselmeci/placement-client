# Dev Container Notes

`devcontainer.json` uses Docker host networking via `"runArgs": ["--network=host"]`,
so the client can be tested against a local placement webapp running on the host machine.
