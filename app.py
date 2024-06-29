from NBA_secrets import *
from flask import Flask, render_template, request
from sqlalchemy import create_engine
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import datetime
from NBA_secrets import *
from langchain.llms import OpenAI
from OPENAI_KEY import api_key

database_type = database_type
dbapi = dbapi
endpoint = endpoint
user = user
password = password
port = port
database = database

app = Flask(__name__)

# Define the database URL
DATABASE_URL = f"{database_type}+{dbapi}://{user}:{password}@{endpoint}:{port}/{database}"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Load data from the database
all_games_df = pd.read_sql("SELECT * FROM all_games_sorted", engine)

# game of the day
#llm = OpenAI(api_key='', max_tokens=1000)

# find games by year

def find_games_by_year(all_games_df, date):
    games_year = all_games_df[all_games_df['GAME_DATE'] == date]
    return games_year

# Function to find games based on general criteria
def find_games_by_general_criteria(all_games_df, criteria):
    if criteria:
        filtered_df = all_games_df[
            (all_games_df['GAME_DATE'] == criteria) |
            (all_games_df['AWAY_TEAM'] == criteria.upper()) |
            (all_games_df['HOME_TEAM'] == criteria.upper())
        ]
        return filtered_df.to_dict(orient='records')
    return []

# Function to save ratings to the database
def save_ratings_to_database(ratings):
    if ratings:
        ratings_df = pd.DataFrame(ratings)
        ratings_df.to_sql("user_rankings_new", engine, schema='public', index=False, if_exists='append')
        return True
    return False

# Route to render the index page and handle search form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    games = None
    criteria = None

    if request.method == 'POST':
        criteria = request.form['criteria']
        try:
            # Try parsing the criteria as a date
            criteria_date = datetime.datetime.strptime(criteria, '%Y-%m-%d').date()
            criteria_str = str(criteria_date)
        except ValueError:
            # If it fails, use it as a string for team abbreviations
            criteria_str = criteria.upper()

        games = find_games_by_general_criteria(all_games_df, criteria_str)

    return render_template('index.html', games=games, criteria=criteria)

# Route to handle ratings submission
@app.route('/rate', methods=['POST'])
def rate():
    ratings = []
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    rating_date = pd.Timestamp.now()

    # Iterate through the form data to find ratings
    for game_id, rating in request.form.items():
        if game_id.startswith('rating_') and rating.strip():  # Check if rating is provided
            game_index = int(game_id.split('_')[1])
            game = request.form[f'game_{game_index}']
            rating = int(rating.strip())
            game_date, matchup, outcome = game.split('|')
            ratings.append({
                'Matchup': matchup,
                'Game date': game_date,
                'Team rated': outcome,
                'Win or loss?': outcome,
                'Rating given': rating,
                'User_First': first_name,
                'User_Last': last_name,
                'Date of rating': rating_date
            })

    if save_ratings_to_database(ratings):
        return "Thanks for your ratings! Ratings have been recorded."
    else:
        return "Please provide at least one valid rating."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)