#!/usr/bin/env python3
"""Generate iCal files for Melissia BC basketball schedules."""

import os
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
import pytz
from jinja2 import Environment, FileSystemLoader

# Base URL for the website
BASE_URL = "https://melissiabc.gr/press.asp?subpage=7&periodID=15&ground=&result="

# Athens timezone
ATHENS_TZ = pytz.timezone('Europe/Athens')


def parse_date(date_str):
    """Parse Greek date format (e.g., '5/10/2025') to datetime object."""
    try:
        # Handle DD/MM/YYYY format
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            # Handle two-digit years
            if year < 100:
                year = year + 2000
            return datetime(year, month, day)
    except:
        pass
    return None


def parse_time(time_str):
    """Parse time string (e.g., '17:00') to time object."""
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
            return hour, minute
    except:
        pass
    return 17, 0  # Default to 17:00


def scrape_schedule():
    """Scrape the basketball schedule from the main page."""
    print("Fetching basketball schedule from main page...")

    try:
        response = requests.get(BASE_URL, timeout=10)
        response.encoding = 'utf-8'  # Ensure proper encoding for Greek text
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all tables
    tables = soup.find_all('table')
    games = []

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')

            # Skip if not enough cells (need at least 10 for all data including τμήμα)
            if len(cells) < 10:
                continue

            # Extract data from cells
            date_str = cells[0].get_text(strip=True)
            time_str = cells[1].get_text(strip=True)
            location_elem = cells[2].find('a')
            location = location_elem.get_text(strip=True) if location_elem else cells[2].get_text(strip=True)
            location_url = location_elem['href'] if location_elem and 'href' in location_elem.attrs else ''

            # Teams info - could be in cell 3 with link or just text
            teams_elem = cells[3].find('a')
            if teams_elem:
                teams = teams_elem.get_text(strip=True)
            else:
                teams = cells[3].get_text(strip=True)

            # Skip header rows or empty rows
            if not date_str or date_str == 'Ημερομηνία' or not re.match(r'\d+/\d+/\d+', date_str):
                continue

            # Parse date and time
            game_date = parse_date(date_str)
            if not game_date:
                continue

            # Check if it's 2025-2026 season (September 2025 to June 2026)
            if not (game_date.year == 2025 and game_date.month >= 9) and \
               not (game_date.year == 2026 and game_date.month <= 6):
                continue

            hour, minute = parse_time(time_str)

            # Combine date and time
            game_datetime = ATHENS_TZ.localize(datetime(
                game_date.year, game_date.month, game_date.day, hour, minute
            ))

            # Extract league/division info (column 8)
            department = ""
            if len(cells) > 8:
                department = cells[8].get_text(strip=True)

            # Extract τμήμα from column 9
            tmima = "Άνδρες"  # Default
            if len(cells) > 9:
                tmima_elem = cells[9].find('a')
                if tmima_elem:
                    tmima = tmima_elem.get_text(strip=True)
                else:
                    # Sometimes it's just text without a link
                    tmima = cells[9].get_text(strip=True)

                # Clean up τμήμα name - remove parentheses content if any
                if tmima:
                    tmima = re.sub(r'\s*\([^)]*\)', '', tmima).strip()

            # Determine if MELISSIA is home or away
            is_home = teams.strip().startswith('ΜΕΛΙΣΣΙΑ') or teams.strip().startswith('Μελίσσια')

            game = {
                'datetime': game_datetime,
                'teams': teams,
                'location': location,
                'location_url': location_url,
                'department': department,
                'tmima': tmima,
                'is_home': is_home
            }

            games.append(game)

    return games


def create_calendar(games, tmima_name):
    """Create an iCal calendar for a specific τμήμα."""
    cal = Calendar()
    cal.add('prodid', '-//Melissia BC//Basketball Schedule//GR')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', f'Melissia BC - {tmima_name}')
    cal.add('x-wr-timezone', 'Europe/Athens')
    cal.add('x-wr-caldesc', f'Πρόγραμμα αγώνων Melissia BC - {tmima_name} (2025-2026)')

    for game in games:
        event = Event()

        # Create event summary
        summary = f"🏀 {game['teams']}"
        if game['is_home']:
            summary = f"🏠 {summary}"
        else:
            summary = f"✈️ {summary}"

        event.add('summary', summary)
        event.add('dtstart', game['datetime'])
        event.add('dtend', game['datetime'] + timedelta(hours=2))  # Assume 2-hour games

        # Add location
        if game['location']:
            event.add('location', game['location'])

        # Create description
        description = f"Παιχνίδι: {game['teams']}\n"
        description += f"Τμήμα: {game['tmima']}\n"
        if game['department']:
            description += f"Κατηγορία: {game['department']}\n"
        if game['location']:
            description += f"Τοποθεσία: {game['location']}\n"
        if game['location_url']:
            description += f"Χάρτης: {game['location_url']}\n"

        event.add('description', description)

        # Add URL if available
        if game['location_url']:
            event.add('url', game['location_url'])

        # Add alarm 1 day before
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('trigger', timedelta(days=-1))
        alarm.add('description', f'Αύριο: {game["teams"]}')
        event.add_component(alarm)

        cal.add_component(event)

    return cal


def sanitize_filename(name):
    """Sanitize filename for filesystem compatibility."""
    # Remove or replace invalid characters
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name.lower()


def create_index_page(calendars_created):
    """Create an HTML page with links to the calendars using Jinja2."""
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html.j2')

    # Calculate total unique games (don't count combined calendar)
    total_games = 0
    for cal in calendars_created:
        if '📅' not in cal['name']:  # Skip combined calendar
            total_games += cal['games']

    # Count τμήματα (excluding combined calendar)
    tmimata_count = sum(1 for cal in calendars_created if '📅' not in cal['name'])

    # Add base URL information for calendar integrations
    # This will be used by JavaScript to create full URLs for calendar subscriptions
    base_url = "https://melissiabc.gr"  # You can modify this to match your actual domain
    
    # Render template
    html = template.render(
        calendars=calendars_created,
        total_games=total_games,
        tmimata_count=tmimata_count,
        base_url=base_url,
        last_updated=datetime.now(ATHENS_TZ).strftime('%d/%m/%Y %H:%M EEST')
    )

    # Write to file
    with open('output/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Created index.html")


def main():
    """Main function to generate calendars."""
    games = scrape_schedule()

    if not games:
        print("No games found for 2025-2026 season.")
        create_index_page([])  # Create empty index page
        return

    print(f"\nFound {len(games)} games for 2025-2026 season.")

    # Group games by τμήμα
    tmimata = {}
    for game in games:
        tmima = game['tmima']
        if tmima not in tmimata:
            tmimata[tmima] = []
        tmimata[tmima].append(game)

    print(f"Found {len(tmimata)} τμήματα:")
    for tmima, tmima_games in sorted(tmimata.items()):
        print(f"  - {tmima}: {len(tmima_games)} games")

    # Create output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    # Generate calendars for each τμήμα
    calendars_created = []
    for tmima_name, tmima_games in sorted(tmimata.items()):
        print(f"\nCreating calendar for {tmima_name} ({len(tmima_games)} games)...")

        # Create calendar
        cal = create_calendar(tmima_games, tmima_name)

        # Save to file (stable filename without period)
        filename = f"melissia-bc-{sanitize_filename(tmima_name)}.ics"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())

        calendars_created.append({
            'name': tmima_name,
            'filename': filename,
            'games': len(tmima_games)
        })

        print(f"  Saved: {filepath}")

    # Create combined calendar with all games
    if len(games) > 0:
        print(f"\nCreating combined calendar with all games ({len(games)} games)...")

        # Sort all games by datetime for better organization
        all_games_sorted = sorted(games, key=lambda g: g['datetime'])

        # Create combined calendar
        cal = create_calendar(all_games_sorted, "Όλα τα Τμήματα")

        # Save to file (stable filename without period)
        filename = "melissia-bc-all.ics"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())

        # Insert at beginning of list for prominence
        calendars_created.insert(0, {
            'name': '📅 Όλα τα Τμήματα',
            'filename': filename,
            'games': len(games)
        })

        print(f"  Saved: {filepath}")

    # Create index.html
    create_index_page(calendars_created)

    print("\nDone! Created calendars:")
    for cal_info in calendars_created:
        print(f"  - {cal_info['name']}: {cal_info['games']} games")


if __name__ == "__main__":
    main()
