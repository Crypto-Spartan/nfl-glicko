import lxml

import sqlite3 as sql
import pandas as pd
import asyncio, aiohttp

conn = sql.connect('nfl_stats.db')
c = conn.cursor()

# Create table
c.execute("""CREATE TABLE seasons (
            year integer, 
            week integer,
            playoffs text, 
            day text, 
            date text, 
            time text,
            winner text,
            loser text,
            hometeam text,
            winner_pts integer,
            winner_yds integer,
            winner_trnovrs integer,
            loser_pts integer,
            loser_yds integer,
            loser_trnovrs integer
        )"""
)

#pd.set_option('display.max_rows', 500)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)

seasons_rows = []

months_shortened = {
    'January':'Jan',
    'February':'Feb',
    'March':'Mar',
    'April':'Apr',
    'May':'May',
    'June':'Jun',
    'July':'Jul',
    'August':'Aug',
    'September':'Sep',
    'October':'Oct',
    'November':'Nov',
    'December':'Dec'
}



def date_shortener(_date):
    month, day = _date.split()
    month = months_shortened.get(month)
    _date = f"{month} {day}"
    return _date



async def fetch(session, year):
    url = f'https://www.pro-football-reference.com/years/{year}/games.htm'
    async with session.get(url) as response:
        url_content = await response.content.read()
        return year, url_content



async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, year) for year in range(1965, 2020)]

        completed = await asyncio.gather(*tasks)
        #for coro in asyncio.as_completed(tasks):

        for year, result in completed:            
            webpage_df = pd.read_html(result)[0]
            
            webpage_df.rename(columns={
                'Unnamed: 5': 'at', 
                'Winner/tie':'Winner', 
                'Loser/tie':'Loser'
                }, inplace=True)
            
            webpage_df = webpage_df[webpage_df['Week'] != 'Week']
            webpage_df.drop('Unnamed: 7', axis=1, inplace=True)
            webpage_df['at'].fillna('', inplace=True)
            
            #webpage_df = webpage_df[webpage_df['Week'].astype('int32', errors='ignore')]

            playoffs_flag = False
            playoff_weeks = set()
            highest_week = 0
            for i, row in enumerate(webpage_df.itertuples()):
                if row.Date == 'Playoffs':
                    playoffs_flag = True
                    continue                
                
                _, week, day, _date, _time, winner, at, loser, pts_W, pts_L, yds_W, to_W, yds_L, to_L = row

                pts_W, yds_W, to_W, pts_L, yds_L, to_L = ( int(pts_W), int(yds_W), int(to_W), 
                                                            int(pts_L), int(yds_L), int(to_L) )

                _date = date_shortener(_date)

                if at == '@':
                    hometeam = 'loser'
                elif at == 'N':
                    hometeam = 'neutral'
                elif at == '':
                    hometeam = 'winner'
                else:
                    raise ValueError(f"'at' value not '@', 'N', or ''.")

                if playoffs_flag:
                    playoffs = week
                    if week not in playoff_weeks:
                        playoff_weeks.add(week)
                        highest_week += 1
                      
                else:
                    highest_week = int(week)
                    playoffs = ''

                week = highest_week
                row = (year, week, playoffs, day, _date, _time, winner, loser, hometeam, pts_W, yds_W, to_W, pts_L, yds_L, to_L)
                seasons_rows.append(row)


            #season = webpage_df[webpage_df['Week'].apply(isinstance, args = [int])]
            #print(len(webpage_df))
            
            #webpage_df = webpage_df.Week
            #print(webpage_df.head(20))
            #print(webpage_df.tail(15))

            #print(season.head(20))
            #print(season.tail(15))
            print(year)
            #print('\n'*3)
            #print('-'*100)



asyncio.get_event_loop().run_until_complete(main())

c.executemany("INSERT INTO seasons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", seasons_rows)

#for x in seasons_rows:
#    print(x)

conn.commit()
conn.close()