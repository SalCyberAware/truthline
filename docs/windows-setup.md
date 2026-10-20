# Running Truthline on Windows (no install step needed)

Tested on Windows 11 with Python 3.10.

## One-time setup
Open Command Prompt (Windows key, type `cmd`, Enter) and run, one line at a time:

    python --version                                  (needs 3.10 or newer)
    python -m venv %USERPROFILE%\truthline-venv       (a private toolbox for this project)
    %USERPROFILE%\truthline-venv\Scripts\activate     (the prompt now starts with (truthline-venv))
    pip install pillow

Keep the toolbox outside OneDrive so it does not try to sync thousands of tool files.

## Every time you open a new window
    %USERPROFILE%\truthline-venv\Scripts\activate
    cd %USERPROFILE%\OneDrive\Documents\GitHub\truthline
    set PYTHONPATH=src
    set PYTHONDONTWRITEBYTECODE=1

`PYTHONPATH=src` tells Python where the Truthline code lives, so no install is needed.
`PYTHONDONTWRITEBYTECODE=1` stops Python writing cache folders into the project (see below).

## Check a file
    python -m truthline.cli check "path\to\file.png" --as "a screenshot of a text message"
    python -m truthline.cli check "path\to\file.png" --as "a screenshot" --json --out %USERPROFILE%\case.json
    python -m truthline.cli draft %USERPROFILE%\case.json --to ic3 --name "Your Name"

## Why `pip install -e .` fails here, and what to do
If your project folder is inside Documents, Windows' ransomware shield (Controlled folder access) can block
`python.exe` from creating folders there. `pip install -e .` then stops at "could not create
'src\truthline.egg-info'". Windows Security > Protection history shows "Protected folder access blocked ...
python.exe". Nothing is wrong; the shield is working.

Options, safest first:
1. Do what this page says: run from the folder with `PYTHONPATH=src` (reading is allowed; no writes needed).
2. Keep anything Python must write (benchmark samples, case files) outside Documents, Desktop and Pictures,
   for example `C:\truthline-data`. See `benchmark/SAMPLE-COLLECTION-GUIDE.md`.
3. Allow your toolbox's Python through Controlled folder access. This lets that Python write to every
   protected folder, so only do it if you trust everything you run with it.

## Handy
- Clear the window: `cls` (not `clear`).
- Sample images should live outside any cloud-synced folder; they are other people's consented files.
