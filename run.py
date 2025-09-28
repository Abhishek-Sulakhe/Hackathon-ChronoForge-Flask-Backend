# run.py
from aura_flow import app

if __name__ == '__main__':
    # Use debug=False in a production environment
    app.run(debug=True, port=5001)