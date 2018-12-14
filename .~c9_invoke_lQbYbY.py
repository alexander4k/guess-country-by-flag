import os
import json
from flask import Flask, render_template, request, redirect, url_for 
from utils import countries, files, game_single, misc, users
import random
import time

app = Flask(__name__)

file_path_single = "data/users.json"


@app.route("/", methods=["GET", "POST"])
def index():
    
    if request.method == "POST":
        if request.form["action"] == "Play alone":
            return redirect(url_for("signIn"))
        else:
            return redirect(url_for("createRoom"))
    return render_template("index.html")


  
@app.route("/sign-in", methods=["GET", "POST"])
def signIn():
    username_error = None
    password_error = None
    if request.method == "POST":
        if request.form["action"] == "Enter game":
            if users.check_if_password_matches(file_path_single, request.form["username"], request.form["password"]):
                return redirect(url_for("gameMenu", username=request.form["username"]))
            elif users.check_if_username_does_exist(file_path_single, request.form["username"]):
                username_error = "A user with this username does not exist"
            else:
                password_error = "Wrong password, try again"
            
    return render_template("sign-in.html", password_error=password_error, username_error=username_error)


   
@app.route("/sign-up", methods=["GET", "POST"])
def signUp():
    username_error = None
    list_of_countries = []
    if request.method == "POST":
        if users.check_if_username_does_exist(file_path_single, request.form["username"]):
            users.add_user_to_data_file(file_path_single, request.form["username"], request.form["password"], game_single.create_game_object())
            
            return redirect(url_for("gameMenu", username=request.form["username"]))
        else:
            username_error = "Username is taken"
    return render_template("sign-up.html", username_error=username_error)


   
@app.route("/game-menu/<username>", methods=["GET", "POST"])
def gameMenu(username):
    if request.method == "POST":
        if "play" in request.form:
            return redirect(url_for("gameSingle", username=username))
        elif "leaderboard" in request.form:
            return redirect(url_for("leaderboard", username=username))
        else:
            return redirect(url_for("index"))
    return render_template("game-menu.html")



@app.route("/create-room", methods=["GET", "POST"])
def createRoom():
    if request.method == "POST":
        files.create_data_file(request.form["game_name"])
        return redirect(url_for("addPlayers", game_name=request.form["game_name"]))
    return render_template("create-room.html")

 
    
@app.route("/add-players/<game_name>", methods=["GET", "POST"])
def addPlayers(game_name):
    username_error = None
    number_of_players_error = None
    
    with open(files.create_file_path(game_name), "r") as json_data:
        player_list = json.load(json_data)
        
    if request.method == "POST":
        for i in range(5):
            if str(i) in request.form:
                users.remove_user_from_data_by_index(files.create_file_path(game_name), i)
                return redirect(url_for("addPlayers", game_name=game_name))
        if "action" in request.form:
            files.delete_data_file(game_name)
            return redirect(url_for("gameMulti"))
        elif "username" in request.form:
            if users.check_number_of_multi_users(files.create_file_path(game_name)) == False:
                if users.check_if_username_does_exist(files.create_file_path(game_name), request.form["username"]):
                    users.add_user_to_data_file(files.create_file_path((game_name)), request.form["username"], "none", game_single.create_game_object())
                    return redirect(url_for("addPlayers", game_name=game_name))
                else:
                    username_error = "Username is taken"
            else:
                number_of_players_error = "The maximum number of players has been reached"
            
    return render_template("add-players.html", username_error=username_error, number_of_players_error=number_of_players_error, player_list=player_list)



@app.route("/game-single/<username>", methods=["GET", "POST"])
def gameSingle(username):
    
    start_time = time.time()
    
    user_score = users.return_user_score(username)
    
    question_num = game_single.extract_key_value_from_game_obj(username, "question_number")
    list_of_countries = game_single.extract_key_value_from_game_obj(username, "countries")
    points = game_single.extract_key_value_from_game_obj(username, "points")
    incorrect_answers = game_single.extract_key_value_from_game_obj(username, "incorrect_answers")
    
    round_country = list_of_countries[question_num - 1]
    
    flag = countries.return_value_for_key_in_country_object_of_index("testCountries", round_country, "flag")
    official_name = countries.return_value_for_key_in_country_object_of_index("testCountries", round_country, "name-official")
    common_name = countries.return_value_for_key_in_country_object_of_index("testCountries", round_country, "name-common")
    
    
    if points == 0:
        game_single.increase_question_number(username)
        game_single.reset_incorrect_answers(username)
        game_single.reset_round_points(username)
        return redirect(url_for("gameSingle", username=username))
    
    
           
    
    if request.method == "POST":
        if request.form["answer"]:
            if question_num == 2 and (request.form["answer"] == official_name or request.form["answer"] == common_name):
                elapsed_time = start_time - time.time()
                
                users.increase_user_score(username, points)
                win = True
                return redirect(url_for("leaderboard", username=username))
            else:
                if request.form["answer"] == official_name or request.form["answer"] == common_name:
                    game_single.increase_question_number(username)
                    users.increase_user_score(username, points)
                    game_single.reset_incorrect_answers(username)
                    game_single.reset_round_points(username)
                    return redirect(url_for("gameSingle", username=username))
                else:
                    game_single.append_incorrect_answers(username, request.form["answer"])
                    game_single.decrease_round_points(username)
                    return redirect(url_for("gameSingle", username=username))
        elif "give-up" in request.form or "play-again" in request.form:
            game_single.reset_question_number(username)
            game_single.reset_incorrect_answers(username)
            game_single.reset_round_points(username)
            users.reset_user_score(username)
            return redirect(url_for("gameSingle", username=username))
        else:
            game_single.increase_question_number(username)
            game_single.reset_incorrect_answers(username)
            game_single.reset_round_points(username)
            return redirect(url_for("gameSingle", username=username,)) 
    
    return render_template("game-single.html", 
                            username=username,
                            flag_url=flag,
                            question_number=question_num,
                            round_points=points,
                            incorrect_answers=incorrect_answers,
                            score=user_score)
    
    
    
@app.route("/leaderboard/<username>", methods=["GET", "POST"])
def leaderboard(username):
    game_single.set_win_state(username, False)
    win = game_single.extract_key_value_from_game_obj(username, "win")
    user_score = users.return_user_score(username)
    leaderboard_data = files.read_data_file("leaderboard")
    # user_rank = leaderboard.extract_rank(username)
    
    if request.method == "POST":
        if "play-again" in request.form:
            game_single.reset_question_number(username)
            game_single.reset_incorrect_answers(username)
            game_single.reset_round_points(username)
            users.reset_user_score(username)
            game_single.set_win_state(username, False)
            return redirect(url_for("gameSingle", username=username))
            
    return render_template("leaderboard-single.html", username=username, win=win, score=user_score, leaderboard_data=leaderboard_data)

    
if __name__ == "__main__":
    app.run(host = os.environ.get("IP"),
            port = int(os.environ.get("PORT")),
            debug = True)
            

