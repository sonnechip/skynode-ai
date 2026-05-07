# Contribution Guidelines

Welcome to the **SkyNode AI** team! To ensure a smooth development process during the AMD Hackathon, please follow these guidelines.

### 🌳 Branching Strategy
We use a **Feature Branch Workflow** to keep our codebase organized and stable.

#### 1. Branch Types
* **main**: The **production-ready** branch. Only merge here when the feature is fully tested and ready for the demo.
* **dev**: The **primary integration** branch. All features should be merged here first for testing.
* **feature/[name]-[task]**: Your **personal workspace** (e.g., `feature/sonnechip-dashboard`).

#### 2. Workflow
1. **Sync**: Always **pull the latest main** before starting.
2. **Branch**: Create your **feature branch**.
3. **Develop**: **Commit** your changes locally.
4. **Push**: Upload your **feature branch** to GitHub. **Never push to main or dev directly**. 
5. **PR**: Open a **Pull Request (PR)** to merge your changes into the dev or main branch.

### 📝 Commit Message Convention
We follow the **Conventional Commits** standard to maintain a clear project history.

**Format:** `type(scope): description`

#### Standard Types
* **feat**: A **new feature** (e.g., `feat(dashboard): add flight table`)
* **fix**: A **bug fix** (e.g., `fix(agent-intent): fix time parsing`)
* **docs**: **Documentation** changes only (e.g., `docs: update readme`)
* **style**: Changes that **do not affect the meaning of the code** (white-space, formatting, missing semi-colons, etc).
* **refactor**: A code change that **neither fixes a bug nor adds a feature**.
* **perf**: A code change that **improves performance** (especially for **AMD NPU**).
* **chore**: Updates to **build tasks, package manager configs**, etc. (e.g., updating `.gitignore`).

### 🔄 Pull Request (PR) Process
All code changes **must be reviewed** through a Pull Request.

1. **No Direct Commits**: **Never push directly** to main or dev.
2. **Self-Review**: Check your code for **print statements** or **hardcoded credentials** before opening a PR.
3. **Review**: At least **one other team member** should glance at the PR for major logic changes.
4. **Merge**: Once approved, use **"Squash and merge"** to keep the history clean.

### 💻 Coding Standards
* **Python (PEP 8)**: Follow standard Python styling. Use **meaningful variable names**.
* **Modularity**: Keep your code **within your designated folder** (`agent-intent/`, `dashboard/`, etc.).
* **Data Contract**: If you change the **shared data structure** in `data.py`, you **MUST notify the team immediately** to ensure interface compatibility.

### 🛠️ Environment & Security
* **Local Vault**: Do **NOT** upload any **real passport numbers or API keys** to GitHub. Use **environment variables** (`.env`).
* **AMD Hardware**: When optimizing for **AMD Acceleration**, document your steps in the `hardware/` folder.