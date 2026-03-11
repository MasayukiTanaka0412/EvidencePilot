# Evidence Pilot

Evidence Pilot is a Windows-compatible Python CLI tool for manual testers. It connects to Azure DevOps Test Plans, loads a test case using Suite ID and Case ID, guides the tester step-by-step in the terminal, and captures full-monitor screenshots as execution evidence.

## Features

- Loads Azure DevOps connection and capture settings from `config.json`
- Detects connected monitors and lets you select one for capture
- Retrieves suite and case information from Azure DevOps Test Plans
- Displays test steps and expected results in English
- Guides test execution with simple commands (`E`, `N`, `S`, `Q`)
- Saves screenshots in structured folders and sanitized filenames
- Handles errors with clear messages and logs details to `evidence_pilot.log`

## Requirements

- Python 3.11+
- Windows (primary target), but development/testing is possible on other platforms
- Azure DevOps project access and a Personal Access Token (PAT) with permissions to read Test Plans and Work Items

## Setup

1. Clone or copy this project.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create your runtime config from the sample:

   ```bash
   copy config.sample.json config.json
   ```

   On PowerShell:

   ```powershell
   Copy-Item config.sample.json config.json
   ```

4. Edit `config.json` and set the values:

   - `AZDO_ORG_URL`
   - `AZDO_PROJECT`
   - `AZDO_PAT`
   - `CAPTURE_ROOT`
   - `STEP_NAME_MAX_LENGTH`

### How to get `AZDO_PAT`

1. Sign in to your Azure DevOps organization at `https://dev.azure.com/{your-organization}`.
2. Click your profile picture in the top-right corner and select **Personal access tokens**. or Visit `https://dev.azure.com/{your-organization}/_usersSettings/tokens`
3. Click **+ New Token**.
4. Fill in the form:
   - **Name**: give it a descriptive name (e.g., `EvidencePilot`)
   - **Organization**: select the organization Evidence Pilot will connect to
   - **Expiration**: choose an appropriate expiry date
   - **Scopes**: select **Custom defined**, then grant at minimum:
     - **Test Management** → Read
     - **Work Items** → Read
5. Click **Create** and copy the token value immediately — it is shown only once.
6. Paste the token as the value of `AZDO_PAT` in `config.json`.

## Example `config.json`

```json
{
  "AZDO_ORG_URL": "https://dev.azure.com/your-organization",
  "AZDO_PROJECT": "your-project",
  "AZDO_PAT": "your-personal-access-token",
  "CAPTURE_ROOT": "captures",
  "STEP_NAME_MAX_LENGTH": 40
}
```

## Run Evidence Pilot

```bash
python main.py
```

## Usage Flow

1. Evidence Pilot loads and validates `config.json`.
2. It detects connected monitors and shows the monitor list.
3. You select one monitor for full-screen screenshot capture.
4. You enter Suite ID and Case ID.
5. Evidence Pilot fetches suite/case details and test steps from Azure DevOps.
6. You confirm whether the loaded case is correct.
7. Step execution mode starts.
8. At each step, use one of the commands below.

## Commands in Step Execution Mode

- `E` — Capture screenshot of the selected monitor
- `N` — Move to next step
- `S` — Return to Suite ID / Case ID selection
- `Q` — Quit the application

When `N` is pressed on the final step, Evidence Pilot prints `Case completed.` and returns to Suite ID / Case ID selection.

## Screenshot Storage Rules

Base directory:

```text
{CAPTURE_ROOT}/{Suite ID}_{Suite Name}/{Case ID}_{Case Name}/
```

File name:

```text
{Step No}_{Step Content}_{Sequence:02}.png
```

Examples:

- `captures/12_LoginSuite/105_ValidLogin/01_Open login page_01.png`
- `captures/12_LoginSuite/105_ValidLogin/01_Open login page_02.png`
- `captures/12_LoginSuite/105_ValidLogin/02_Login success_01.png`

Sequence resets per step and is always 2 digits.

## Troubleshooting

- **Missing `config.json`**: Create it from `config.sample.json` and fill required keys.
- **Invalid config values**: Ensure all required keys are present and `STEP_NAME_MAX_LENGTH` is a positive integer.
- **Azure DevOps errors**: Confirm URL/project/PAT and PAT permissions.
- **Suite or case not found**: Verify IDs and that the test case belongs to the selected suite.
- **No monitor detected**: Check OS display settings and monitor connections.
- **Screenshot save failure**: Verify write permission for `CAPTURE_ROOT` and available disk space.

Detailed diagnostics are written to `evidence_pilot.log`.

## Build a Windows Executable (PyInstaller)

Install PyInstaller:

```bash
pip install pyinstaller
```

Basic build command:

```bash
pyinstaller --onefile main.py
```

Recommended command (custom executable name):

```bash
pyinstaller --onefile --name "evidence-pilot" main.py
```

The executable will be generated in the `dist` folder.

## Non-goals

Evidence Pilot intentionally does **not** implement:

- Azure DevOps upload of screenshots
- OCR
- Image editing
- GUI
