from flask import Flask ,jsonify
import json

app = Flask(__name__)

def show_states_id():
    try:
        with open('state_codes.json', 'r', encoding='utf-8') as file:
         data = json.load(file)
         return data
    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

@app.route('/states', methods=['GET'])
def get_states():
    return jsonify(show_states_id())


if __name__ == '__main__':
    app.run(debug=True)
