import sqlite3 as sql

conn = sql.connect('nfl-stats.db')
c = conn.cursor()

teams_set = set()

old_team_remap = {
    'St. Louis Cardinals':'Arizona Cardinals',
    'Phoenix Cardinals':'Arizona Cardinals',
    'San Diego Chargers':'Los Angeles Chargers',
    'Baltimore Colts':'Indianapolis Colts',
    'Tennessee Oilers':'Tennessee Titans',
    'Houston Oilers':'Tennessee Titans',
    'Boston Patriots':'New England Patriots',
    'Los Angeles Raiders':'Las Vegas Raiders',
    'Oakland Raiders':'Las Vegas Raiders',
    'St. Louis Rams':'Los Angeles Rams'
}

for row in c.execute('SELECT * FROM regular_season'):
    winner = row[5]
    loser = row[6]

    for team in (winner, loser):
        teamcheck = old_team_remap.get(team)

        if teamcheck:
            team = teamcheck

        teams_set.add(team)

print(len(teams_set))

for x in sorted(teams_set, key=lambda x: x.split()[-1]):
    print(x)