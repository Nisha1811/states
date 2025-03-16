import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import json
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy # type: ignore

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# State Model
class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String(100), nullable=False, unique=True)
    state_code = db.Column(db.String(10), nullable=False, unique=True)

    def __repr__(self):
        return f"<State {self.state_name}>"

# Scrape Data 
@app.route('/scrape', methods=['GET'])
def scrape_data():

    url = "https://kb.bullseyelocations.com/article/60-india-state-codes"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if status code != 200
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch data: {e}"}), 500

    states = []

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')

    if table:
        rows = table.find_all('tr')[1:]  

        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 2:
                state_name = columns[0].text.strip()
                state_code = columns[1].text.strip()

                states.append({
                    'State Name': state_name,
                    'ID': state_code
                })

    # Save scraped data to JSON
    with open('state_codes.json', 'w', encoding='utf-8') as file:
        json.dump(states, file, indent=4, ensure_ascii=False)

    return jsonify({"message": f"Successfully scraped {len(states)} states and saved to 'state_codes.json'."})

# Verify Data
@app.route('/verify', methods=['GET'])
def verify_data():
    try:
        with open('state_codes.json', 'r') as file:
            states_data = json.load(file)

        verified_data = []
        invalid_data = []

        for item in states_data:
            state_name = item.get('State Name')
            state_code = item.get('ID')

            if state_name and state_code and len(state_code) == 2:
                verified_data.append(item)
            else:
                invalid_data.append(item)

        # Save verified data
        with open('verified_state_codes.json', 'w', encoding='utf-8') as file:
            json.dump(verified_data, file, indent=4, ensure_ascii=False)

        return jsonify({
            "message": f"Successfully verified {len(verified_data)} valid entries.",
            "invalid_entries": invalid_data
        })

    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Error: 'state_codes.json' is missing or invalid format."}), 500

#  InsertData into Database
@app.route('/insert', methods=['GET'])
def insert_data():
    try:
        with open('verified_state_codes.json', 'r') as file:
            states_data = json.load(file)

        inserted_count = 0
        for item in states_data:
            state_name = item.get('State Name')
            state_code = item.get('ID')

            if state_name and state_code and not State.query.filter_by(state_code=state_code).first():
                state = State(state_name=state_name, state_code=state_code)
                db.session.add(state)
                inserted_count += 1

        db.session.commit()
        return jsonify({"message": f"Successfully inserted {inserted_count} states into the database."})

    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": " Error: 'verified_state_codes.json' is missing or invalid format."}), 500

# GET:Show All States from Database
@app.route('/states', methods=['GET'])
def get_states():
    """Display all state data from the database."""
    all_states = State.query.all()
    return jsonify([
        {"State Name": state.state_name, "State Code": state.state_code}
        for state in all_states
    ])

#Database Creation
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
