# Import the create_app function from the web module
from web import create_app

# Create an instance of the Flask application
app = create_app()

# Entry point for running the application
if __name__ == "__main__":
    app.run(debug=True)