# Hangman-API

## Game Description:
This is a hangman like mini-game. The player have limited chances to guess a word. The game will ends when the player have successfully or fail to guess the word within the guessing limits.

## HangmanApi Description:
This Api provides endpoints for you to develope your own Hangman like applications.

## Quick Start Instructions:
1. Update the value of application in app.yaml to app ID you have registered in the App Engine admin console.
1. Run the app with devserver using dev_appserver.py DIR or GoogleAppEngine launcher. visit '''localhost:8080''' to ensure its running.
1. visit API explorer through this url: '''localhost:8080/_ah/api/explorer'''

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, attempts, answer
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Attempts
    has to be greater than 1, letter in answer has to be greater than
    1 as well.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, move
    - Returns: GameForm with new game state.
    - Description: Accepts a 'move' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    It also stores player's move history.
    
 - **get_user_games**
    - Path: '/user/{user_name}/games'
    - Method: GET
    - Parameters: user_name, email
    - Returns: StringMessage. 
    - Description: Returns all games recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **cancel_game**
    - Path: '/game/{urlsafe_game_key}'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage. 
    - Description: Delete game record which provide by urlsafe_game_key
    Will raise a NotFoundException if the game does not exist.
    Will raise a BadRequestException if the game already over.

- **get_high_wins**
    - Path: '/high_wins'
    - Method: GET
    - Parameters: message_types.VoidMessage
    - Returns: UserForms
    - Description: Rank player based on the number of their wins.
    Will raise a NotFoundException if there's no user in the datastore.

- **get_user_ranking**
    - Path: '/get_user_ranking'
    - Method: GET
    - Parameters: message_types.VoidMessage
    - Returns: UserForms
    - Description: Rank player based on their winning rate.
    Will raise a NotFoundException if there's no user in the datastore.

- **get_game_history**
    - Path: '/game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: message_types.VoidMessage
    - Returns: GameHistory
    - Description: Return user's move history for the game with message and guess.
    Will raise a NotFoundException if there's no game matching the url safe key in the datastore.

## Models Included:
 - **User**
    - Stores unique user_name, email, wins and total_played.

 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

## Forms Included:
 - **GameForm**
    - Game's state (urlsafe_key, attempts_remaining, game_over flag, message, user_name)
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Create new game (user_name, answer, attempts)
 - **MakeMoveForm**
    - Make a move form (user_name, move)
 - **ScoreForm**
    - Score's state (user_name, date, won, attempts_remaining)
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **UserForm**
    - Representation of user's information (name, email, wins, total_played, win_percentage)
 - **UserForms**
    - Multiple UserForm container.
 - **GameHistory**
    - Game moves container.






