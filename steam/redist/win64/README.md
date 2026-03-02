# VC++ Redistributable — do not commit binaries here

Place `vcredist_x64.exe` (Microsoft Visual C++ 2022 Redistributable, x64)
in this directory before running the Steam depot build.

**Download:** https://aka.ms/vs/17/release/vc_redist.x64.exe

The CI workflow (`steam-upload.yml`) downloads this file automatically from
the Microsoft URL during the build step, so you do not need to commit it.
The file is excluded from version control via `.gitignore`.
