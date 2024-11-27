from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
  
    app = Flask(__name__, static_folder='static', static_url_path='/static')  # this is the name of the module/package that is calling this app
    # Should be set to false in a production environment
    app.debug = True
    app.secret_key = 'somesecretkey'
    # set the app configuration data 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
    # initialise db with flask app
    db.init_app(app)

    Bootstrap(app)
    
    # initialise the login manager
    login_manager = LoginManager()
    
    # set the name of the login function that lets user login
    # in our case it is auth.login (blueprintname.viewfunction name)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # create a user loader function takes userid and returns User
    # Importing inside the create_app function avoids circular references
    with app.app_context():
        from .models import User, SearchEvent
        db.create_all()
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        from .views import main_bp
        app.register_blueprint(main_bp)

        from .auth import auth_bp
        app.register_blueprint(auth_bp)


    #404 Error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    #500 Error handler
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app