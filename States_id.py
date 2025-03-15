import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy  # type: ignore

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# State Model
class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String(100), nullable=False)
    state_code = db.Column(db.String(10), nullable=False, unique=True)

    def __repr__(self):
        return f"<State {self.state_name}>"

# Function to load data from JSON to Database
def load_data():
    try:
        with open('state_codes.json', 'r') as file:
            states_data = json.load(file)

        for item in states_data:
            if not State.query.filter_by(state_code=item['ID']).first():
                state = State(state_name=item['State Name'], state_code=item['ID'])
                db.session.add(state)
        db.session.commit()

    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: JSON file is missing or invalid format.")

# Create tables and load data
with app.app_context():
    db.create_all()
    load_data()

# GET :Show all states
@app.route('/states', methods=['GET'])
def get_states():
    return jsonify(states)

# GET Route :Get state details by name
@app.route('/states/<string:state_name>', methods=['GET'])
def get_state_by_name(state_name):
    state = State.query.filter_by(state_name=state_name.title()).first()

    if state:
        return jsonify({
            "State_Name": state.state_name,
            "State_Code": state.state_code
        })
    else:
        return jsonify({"error": "State not found"}), 404

#  POST:Add New State Data
@app.route('/states', methods=['POST'])
def add_state():
    data = request.json
    state_name = data.get('state_name')
    state_code = data.get('state_code')

    # Validation for missing data
    if not state_name or not state_code:
        return jsonify({"error": "State name and code are required"}), 400

    #  Check for duplicate entry
    if State.query.filter_by(state_name=state_name.title()).first():
        return jsonify({"error": "State already exists"}), 409

    # Add new state
    new_state = State(state_name=state_name.title(), state_code=state_code.upper())
    db.session.add(new_state)
    db.session.commit()

    return jsonify({
        "message": "State added successfully",
        "State_Name": new_state.state_name,
        "State_Code": new_state.state_code
    }), 201

# Scraping  for State Data
url = "https://kb.bullseyelocations.com/article/60-india-state-codes"

response = requests.get(url)
states = []

if response.status_code == 200:
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

print(f"✅ Successfully scraped {len(states)} states and saved to 'state_codes.json'")

if __name__ == '__main__':
    app.run(debug=True)
