from flask import Blueprint, request
from flask.templating import render_template
from . import conn

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html")

@views.route('/games')
def games():
    cur = conn.cursor()
    cur.execute("select gameID, allGames.* from game join allGames on game.date = allGames.date")
    data = cur.fetchall()
    return render_template("games.html", data=data)

@views.route('/games/<game_id>')
def games_withid(game_id):
    cur = conn.cursor()
    player_table = """select playerName, position, championName, visionScore, assists, kills, totalGold, deaths, totalCS, damageToChampions, DMP 
                from player natural join participates natural join plays natural join team
                {} and side = "{}"
                order by position="top" desc, position="jng" desc, position="mid" desc, position="bot" desc, position="sup" desc;"""
    
    if game_id:
        query = "where gameID = \"{}\"".format(game_id.replace('%2F', '/'))
    else:
        query = ""
    
    cur.execute("select date, length/60 as game_length, IIF(result == 1, 'Blue Win', 'Red Win') win from game {};".format(query))
    game_data = cur.fetchall()
    cur.execute("select championName from banned {};".format(query))
    bans = cur.fetchall()
    cur.execute("select side, teamName, league, tKills, tDeaths, dragons, heralds, barons, towers, inhibitors from team natural join plays {};".format(query))
    team = cur.fetchall()
    cur.execute(player_table.format(query, "Blue"))
    blue = cur.fetchall();
    cur.execute(player_table.format(query, "Red"))
    red = cur.fetchall();
    return render_template("game.html", game_data=game_data, team=team, bans=bans, blue=blue, red=red)

@views.route('/champions')
def champs():
    cur = conn.cursor()
    cur.execute("Select * from champion")
    data = cur.fetchall()
    return render_template("champs.html", data=data)

@views.route('/teams', methods=["POST","GET"])
def team():
    cur = conn.cursor()
    if request.method == "POST":
        league = request.form['leagues']
        range_min = request.form['min']
        range_max = request.form['max']
        if league == "All":
            query = ""
        else:
            query = "where team.league = \"" + league + "\" "
        
        if not range_min:
            range_min = 0
        if not range_max:
            range_max = 1000
    else:
        query = ""
        range_min = 0
        range_max = 1000
    
    cur.execute("select teamName, league, count(plays.gameID) as games_played from team natural join plays {} group by teamName, league having games_played >= {} and games_played <= {};".format(query, range_min, range_max))
    data = cur.fetchall()
    cur.execute("select DISTINCT league from team;")
    leagues = cur.fetchall()
    return render_template("team.html", data=data, leagues=leagues)

@views.route('/players')
def player():
    cur = conn.cursor()
    cur.execute("select playerName, position, teamName from player join team on player.teamID = team.teamID;")
    data = cur.fetchall()
    return render_template("player.html", data=data)

@views.route('/players/<player_name>')
def player_info(player_name):
    cur = conn.cursor()
    player_info = """select playerName, position, teamName, league from player natural join team
                    where playerName = \"{}\";""".format(player_name)
    games_table = """select distinct gameID, championName, length/60 as length, 
                    IIF(((result == 1 and side == "Blue") or (result == 0 and side == "Red")), 'Win', 'Lose') as result 
                    from game natural join player natural join team natural join participates natural join plays
                    where playerName = \"{}\"
                    order by date;""".format(player_name)
    win_rate_table = """select championName, num_games, wins*100.0/num_games as winRate 
                        from playerGamesWins
                        where playerName = \"{}\";""".format(player_name)
    
    cur.execute(games_table)
    game_data = cur.fetchall()
    cur.execute(win_rate_table)
    win_rate_table = cur.fetchall()
    cur.execute(player_info)
    info = cur.fetchall()
    return render_template("player_info.html", game_data=game_data, player=player_name, wins=win_rate_table, info=info)

@views.route('/positions', methods=["POST","GET"])
def position():
    cur = conn.cursor()
    if request.method == "POST":
        average = request.form['average']
        if average == "Average KDA":
            query = "avg(kills)+avg(assists)/avg(deaths)"
        elif average == "Average Total Gold":
            query = "avg(totalGold)"
        elif average == "Average Vision Score":
            query = "avg(visionScore)"
        elif average == "Average Damage Dealt Per Minute":
            query = "avg(damageToChampions)"
        else:
            query = "avg(DMP)"
    else:
        average = "Average KDA"
        query = "avg(kills)+avg(assists)/avg(deaths)"
    
    print(average)
    cur.execute("select position, {} as Average from player natural join participates group by position order by Average desc;".format(query))
    data = cur.fetchall()    
    return render_template("position.html", data=data, ave=average)

@views.route('/bans')
def bans():
    cur = conn.cursor()
    cur.execute("""select champion.championName, count(banned.championName)*100.0/12044 as banRate
                from champion left join banned on champion.championName = banned.championName
                group by champion.championName;""")
    data = cur.fetchall()
    return render_template("bans.html", data=data)


@views.route('/wins')
def wins():
    cur = conn.cursor()
    cur.execute("""select champion.championName, num_games, num_wins*100.0/num_games as winRate 
                from champion left join numWins on champion.championName = numWins.championName 
                left join numGames on numWins.championName = numGames.championName;""")
    data = cur.fetchall()
    return render_template("wins.html", data=data)

@views.route('/leader', methods=["POST","GET"])
def leader():
    cur = conn.cursor()
    
    if request.method == "POST":
        champ = request.form['champ']
    else:
        champ = "Aatrox"
    
    cur.execute("""select playerName, position, teamName, league, count(*) as champ_count from player natural join participates
                natural join team
                where participates.championName = "{}"
                group by playerName, position, teamName, league
                order by champ_count desc limit 3;""".format(champ))
    data = cur.fetchall()
    cur.execute("select championName from champion;")
    champs = cur.fetchall()
    return render_template("leader.html", data=data, champs=champs, champ=champ)

@views.route('/kda-ranking', methods=["POST","GET"])
def kda():
    cur = conn.cursor()
    if request.method == "POST":
        league = request.form['leagues']
        if league == "All":
            query = ""
        else:
            query = "where team.league = \"" + league + "\" "
    else:
        query = ""
        league = ""
    
    cur.execute("""select playerName, position, avg(kills)+avg(assists)/avg(deaths) as KDA
                from player natural join participates
                natural join team
                {}
                group by playerName
                order by KDA desc;""".format(query))
    data = cur.fetchall()
    cur.execute("select DISTINCT league from team;")
    leagues = cur.fetchall()
    return render_template("kda.html", data=data, leagues=leagues, league=league)
    
    