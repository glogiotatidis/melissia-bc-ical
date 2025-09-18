# Melissia BC Calendar Generator

This project automatically generates iCal calendar files for Melissia Basketball Club games from their website.

## Features

- Fetches all games from the main schedule page
- Automatically groups games by τμήμα (team category) as listed in the schedule
- Creates separate iCal files for each τμήμα discovered:
  - Άνδρες (Men)
  - Γυναίκες (Women)
  - Νέοι Άνδρες U23 (Young Men U23)
  - Νέες Γυναίκες U23 (Young Women U23)
  - Έφηβοι U18 (Junior Boys U18)
  - Νεάνιδες U18 (Junior Girls U18)
  - Παίδες Α U16 (Youth Boys A U16)
  - Κορασίδες Α/Β U16 (Youth Girls A/B U16)
  - And any new categories as they appear
- Creates a combined "📅 Όλα τα Τμήματα" calendar with all games
- Only includes games from the current season (2025-2026)
- Automatically updates daily via GitHub Actions
- Serves calendars via GitHub Pages
- Beautiful web interface using Jinja2 templates
- Proper timezone handling (Europe/Athens)
- Event reminders 1 day before each game

## Local Development

### Prerequisites

- Docker and Docker Compose (or Podman)
- Python 3.11+ (if running without Docker)
- uv package manager (if running without Docker)

### Running with Docker/Podman

```bash
# With Docker Compose
docker-compose build
docker-compose up

# With Podman (recommended)
podman build -t melissia-bc-calendar .
podman run --rm -v ./output:/app/output melissia-bc-calendar

# Note: If podman-compose is not available, use podman directly
```

### Running without Docker

```bash
# Install uv (if not already installed)
pip install uv

# Install dependencies
uv pip install -e .

# Run the script
python src/generate_calendars.py
```

## GitHub Actions

The workflow runs automatically:
- Daily at 06:00 UTC (08:00 Athens time)
- Can be manually triggered from the Actions tab

The workflow:
1. Builds the Docker image
2. Runs the calendar generator
3. Commits any changes to the output directory
4. Deploys to GitHub Pages

## Output

Generated files are saved to the `output/` directory:
- `*.ics` - iCal calendar files for each department
- `index.html` - Web interface for downloading calendars

## Configuration

To use this for your own repository:

1. Fork or copy this repository
2. Enable GitHub Pages in repository settings:
   - Go to Settings → Pages
   - Set source to "GitHub Actions"
3. Enable GitHub Actions:
   - Go to Actions tab
   - Enable workflows
4. Run the workflow manually or wait for daily execution
5. The calendars will be available at `https://[username].github.io/[repository]/`

## Quick Start

```bash
# Clone the repository
git clone https://github.com/[username]/melissia-bc.git
cd melissia-bc

# Run locally with the provided script
./run.sh

# Or manually trigger GitHub Action
# Go to Actions tab → Update Basketball Calendars → Run workflow
```

## Files Generated

- `output/melissia-bc-all-2025-26.ics` - Combined calendar with all games from all τμήματα
- `output/melissia-bc-*.ics` - Individual iCal files for each τμήμα (e.g., `melissia-bc-άνδρες-2025-26.ics`)
- `output/index.html` - Web interface for downloading calendars (generated from Jinja2 template)
- `output/_config.yml` - GitHub Pages configuration

## Technical Details

- **Scraping**: BeautifulSoup4 for HTML parsing
- **Calendar Generation**: iCalendar library with proper timezone support
- **Templates**: Jinja2 for HTML generation
- **Package Management**: uv for fast, reliable Python dependency management
- **Containerization**: Docker/Podman support for consistent execution
# melissia-bc-ical
