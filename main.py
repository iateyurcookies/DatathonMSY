# Main file to run the code
from website import create_app

app = create_app()

# Only let code run when main.py is ran
if __name__ == "__main__":
    app.run(debug=True)