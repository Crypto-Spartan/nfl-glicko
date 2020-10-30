import sqlite3 as sql
from glicko2 import Glicko2, WIN, DRAW, LOSS
import random
from scipy.optimize import differential_evolution, minimize


conn = sql.connect('nfl_stats.db')
c = conn.cursor()

current_teams = (
    'San Francisco 49ers',
    'Chicago Bears',
    'Cincinnati Bengals',
    'Buffalo Bills',
    'Denver Broncos',
    'Cleveland Browns',
    'Tampa Bay Buccaneers',
    'Arizona Cardinals',
    'Los Angeles Chargers',
    'Kansas City Chiefs',
    'Indianapolis Colts',
    'Dallas Cowboys',
    'Miami Dolphins',
    'Philadelphia Eagles',
    'Atlanta Falcons',
    'New York Giants',
    'Jacksonville Jaguars',
    'New York Jets',
    'Detroit Lions',
    'Green Bay Packers',
    'Carolina Panthers',
    'New England Patriots',
    'Las Vegas Raiders',
    'Los Angeles Rams',
    'Baltimore Ravens',
    'Washington Redskins',
    'New Orleans Saints',
    'Seattle Seahawks',
    'Pittsburgh Steelers',
    'Houston Texans',
    'Tennessee Titans',
    'Minnesota Vikings'
)

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


MU = 1500
PHI = 350
SIGMA = 0.06
TAU = 1.0
EPSILON = 0.000001


def run_nfl_glicko(mu=MU, phi=PHI, sigma=SIGMA, tau=TAU, epsilon=EPSILON):

    glicko_obj = Glicko2(mu=mu, phi=phi, sigma=sigma, tau=tau, epsilon=epsilon)
    team_ratings = {}
    #teams_set = set()
    best_team = None
    glicko_overall_total = 0
    glicko_overall_score = 0

    def season_reset(team_ratings):
        
        new_team_ratings = {team: glicko_obj.create_rating( ((rating.mu - 1500) / 2) + 1500 )
                            for team, rating in team_ratings.items() }        

        return new_team_ratings

    for team in current_teams:
        #rating = glicko_obj.create_rating(random.randint(1000,2000), random.randint(50, 350))
        rating = glicko_obj.create_rating()
        team_ratings[team] = rating


    for year in range(1965, 2020):

        team_ratings = season_reset(team_ratings)
        glicko_season_score = 0
        glicko_season_total = 0
        
        for row in c.execute("SELECT * FROM seasons WHERE year = ?", (year,) ):
            #print(row)
            #row = list(row)
            winner = old_team_remap.get(row[6]) or row[6]
            loser = old_team_remap.get(row[7]) or row[7]
            winner_rating = team_ratings[winner]
            loser_rating = team_ratings[loser]
            pts_diff = row[9] - row[12]        

            """print(f"{winner} rating: {winner_rating}")
            print(f"{loser} rating: {loser_rating}")
            print( glicko_obj.quality_1vs1(winner_rating, loser_rating) )"""

            winner_win_pct = glicko_obj.expect_score(winner_rating, loser_rating,                                                 glicko_obj.reduce_impact(winner_rating))
            loser_win_pct = glicko_obj.expect_score(loser_rating, winner_rating,                                                  glicko_obj.reduce_impact(loser_rating))

            #print(f"winner win pct: {winner_win_pct*100}%")
            #print(f"loser win pct: {loser_win_pct*100}%")

            if winner_win_pct > loser_win_pct:
                glicko_season_score += 1
            elif winner_win_pct == loser_win_pct and pts_diff == 0:
                glicko_season_score += 1

            glicko_season_total += 1

            if pts_diff > 0:
                winner_new_rating, loser_new_rating = glicko_obj.rate_1vs1(winner_rating, 
                                                                            loser_rating)
            elif pts_diff == 0:
                winner_new_rating, loser_new_rating = glicko_obj.rate_1vs1(winner_rating, 
                                                                loser_rating, drawn=True)
            else:
                raise ValueError('How can "pts_diff" be negative?')

            team_ratings[winner] = winner_new_rating
            team_ratings[loser] = loser_new_rating

        season_best_team = sorted(team_ratings.items(), key=lambda x: x[1].mu, reverse=True)[0]

        if not best_team:
            best_team = (year,) + season_best_team
        
        elif season_best_team[1].mu > best_team[2].mu:
            best_team = (year,) + season_best_team

        glicko_overall_score += glicko_season_score
        glicko_overall_total += glicko_season_total
        
        #print(year)
        #print(season_best_team)
        #print(f"glicko score: {glicko_season_score}/{glicko_season_total} - {(glicko_season_score/glicko_season_total)*100}%")
        #print('-'*90)


    #print('\n'*3)
    print(f"overall glicko score: {glicko_overall_score}/{glicko_overall_total} - {(glicko_overall_score/glicko_overall_total)*100}%")
    #print(f"best team: {best_team}")
    print('-'*90)

    return glicko_overall_score, glicko_overall_total



#def my_optimizer(phi=PHI, sigma=SIGMA, tau=TAU):
def my_optimizer(params):
    _phi, _sigma, _tau = params
    #_phi = params[0]
    score, total = run_nfl_glicko(mu=MU, phi=_phi, sigma=_sigma, tau=_tau, epsilon=EPSILON)
    print(f"phi: {_phi}, sigma: {_sigma}, tau: {_tau}")
    #print(f"phi: {_phi}")
    return -score


if __name__ == '__main__':
    print('\n'*20)
    print('START')
    print('-'*90)

    """MU = 1500
        PHI = 350
        SIGMA = 0.06
        TAU = 1.0
        EPSILON = 0.000001"""

    #result = differential_evolution(my_optimizer, bounds=((60,70), (0.059,0.07), (0.9, 1.4)), strategy='randtobest1bin', maxiter=100000, popsize=50, recombination=0.5, disp=True, workers=-1)#, init=(350, 0.06, 0.9), workers=1)

    #result = differential_evolution(my_optimizer, bounds=((1, 100),), strategy='randtobest1bin', maxiter=100000, popsize=50, recombination=0.5, disp=True, workers=-1)

    x0 = 65, 0.06, 1.3
    bounds = ((60,70), (0.059,0.07), (0.9, 1.4))

    result = minimize(my_optimizer, x0, bounds=bounds, options={'maxiter':10000,'disp':True})

    print(result)

    #my_optimizer()