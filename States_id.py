
import requests
from bs4 import BeautifulSoup
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

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

# Verify State Data
def verify_data(state_name, state_code):
   
    if not state_name or not state_code:
        return False  
    if len(state_code) != 2:  
        return False  
    return True

#  Scrape Data 
def scrape_data():
   
    url = "https://kb.bullseyelocations.com/article/60-india-state-codes"

    try:
        response = requests.get(url)
        response.raise_for_status()  
    except requests.RequestException as e:
        print(f" Error fetching data: {e}")
        return

    states = []  # Store scraped data

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

    with open('state_codes.json', 'w', encoding='utf-8') as file:
        json.dump(states, file, indent=4, ensure_ascii=False)

    print(f" Successfully scraped {len(states)} states and saved to 'state_codes.json'")

#  Insert Verified Data 
def insert_data():
  
    try:
        with open('state_codes.json', 'r') as file:
            states_data = json.load(file)

        for item in states_data:
            state_name = item.get('State Name')
            state_code = item.get('ID')

            if state_name and state_code and verify_data(state_name, state_code):
                
                if not State.query.filter_by(state_code=state_code).first():
                    state = State(state_name=state_name, state_code=state_code)
                    db.session.add(state)

        db.session.commit()
        print(f" Successfully inserted data into the database.")
    
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: JSON file is missing or invalid format.")

#  Loading the data and create database
with app.app_context():
    db.create_all()

# GET: Show All States
@app.route('/states', methods=['GET'])
def get_states():
    all_states = State.query.all()
    return jsonify([
        {"State Name": state.state_name, "State Code": state.state_code}
        for state in all_states
    ])

# GET: State by Name
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

#POST: Add New State Data
@app.route('/states', methods=['POST'])
def add_state():
    data = request.json
    state_name = data.get('state_name')
    state_code = data.get('state_code')

    if not verify_data(state_name, state_code):
        return jsonify({"error": "Invalid or incomplete data"})

    if State.query.filter_by(state_code=state_code).first():
        return jsonify({"error": "State already exists"})

    # Insert New State
    new_state = State(state_name=state_name.title(), state_code=state_code.upper())
    db.session.add(new_state)
    db.session.commit()

    return jsonify({
        "message": "State added successfully",
        "State_Name": new_state.state_name,
        "State_Code": new_state.state_code
    })

# Scraping and Inserting
@app.route('/scrape', methods=['GET'])
def scrape_route():
    scrape_data()
    return jsonify({"Data successfully scraped and saved to 'state_codes.json'."})

@app.route('/insert', methods=['GET'])
def insert_route():
    with app.app_context(): 
        insert_data()
    return jsonify({"Data successfully inserted into the database."})

if __name__ == '__main__':
    app.run(debug=True)
