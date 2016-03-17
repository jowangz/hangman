import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, GameForms
from models import MakeMoveForm, ScoreForms, UserForms, GameHistory
from utils import get_by_urlsafe

USER_REQUEST = endpoints.ResourceContainer(
                    user_name=messages.StringField(1),
                    email=messages.StringField(2)
                    )
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
                    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
                        MakeMoveForm,
                        urlsafe_game_key=messages.StringField(1),)


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Hangman game api"""
    @endpoints.method(
                    request_message=USER_REQUEST,
                    response_message=StringMessage,
                    path='user',
                    name='create_user',
                    http_method='POST'
                    )
    def create_user(self, request):
        """Creae a user"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exist!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(
                        request_message=NEW_GAME_REQUEST,
                        response_message=GameForm,
                        path='game',
                        name='new_game',
                        http_method='POST'
                        )
    def new_game(self, request):
        """Create a new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        if not request.answer:
            raise endpoints.BadRequestException('please enter the answer!')
        try:
            game = Game.new_game(user.key, request.answer, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Attempts has to be over 1.')

        return game.to_form('Good luck!')

    @endpoints.method(
                        request_message=GET_GAME_REQUEST,
                        response_message=GameForm,
                        path='game/{urlsafe_game_key}',
                        name='get_game',
                        http_method='GET'
                        )
    def get_game(self, request):
        """Return a current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and game.game_over is not True:
            return game.to_form('Time to make a move! {} left'.
                                format(game.attempts_remaining))
        elif game.game_over is True:
            return game.to_form('Game already over')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(
                        request_message=MAKE_MOVE_REQUEST,
                        response_message=GameForm,
                        path='game/{urlsafe_game_key}',
                        name='make_move',
                        http_method='PUT'
                        )
    def make_move(self, request):
        """Make a move, return a game state with a message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('The user does not exist!')
        if len(list(request.move)) > 1:
            raise endpoints.NotFoundException(
                                    'You can only enter 1 character!'
                                    )
        if request.move not in game.answer:
            game.attempts_remaining -= 1
            if game.attempts_remaining < 1:
                user.total_played += 1
                game.end_game(False)
                msg = 'Game Over, you lose!'
            msg = 'Try again, {} try left!'.format(game.attempts_remaining)
        # Check the move is already entered.
        elif request.move in game.answer_check:
            return game.to_form(
                                'You already got this letter {}'.
                                format(request.move)
                                )
        else:
            # Store the move in game.answer_check.
            for i, x in enumerate(game.answer):
                if x == request.move:
                    game.answer_check[i] = request.move
            if game.answer_check == game.answer:
                user.wins += 1
                user.total_played += 1
                game.end_game(True)
                msg = 'You win!'
            else:
                msg = 'Almost there! You got {}'.format(game.answer_check)
        # Add game move history.
        game.move_histories.append(
                                ["{},".format(request.move) + "{}".format(msg)]
                                )
        game.put()
        user.put()
        return game.to_form(msg)

    @endpoints.method(
                        request_message=USER_REQUEST,
                        response_message=ScoreForms,
                        path='scores/user/{user_name}',
                        name='get_user_score',
                        http_method='GET'
                        )
    def get_user_scores(self, request):
        """Return the user's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A user with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        if not scores:
            raise endpoints.NotFoundException(
                    'No score found for this user!'
                    )
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(
                        request_message=USER_REQUEST,
                        response_message=GameForms,
                        path='/user/{user_name}/games',
                        name='get_user_games',
                        http_method='GET'
                        )
    def get_user_games(self, request):
        """Return all user's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.BadRequestException('User not found.')
        games = Game.query(Game.user == user.key)
        return GameForms(items=[game.to_form('') for game in games])

    @endpoints.method(
                        request_message=GET_GAME_REQUEST,
                        response_message=StringMessage,
                        path='/game/{urlsafe_game_key}',
                        name='cancel_game',
                        http_method='DELETE'
                        )
    def cancel_game(self, request):
        """Delete a game.(Game must not have ended)"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and not game.game_over:
            game.key.delete()
            return StringMessage(
                            message='Game with key: {} deleted.'.
                            format(request.urlsafe_game_key)
                                )
        elif game and game.game_over:
            raise endpoints.BadRequestException('Game is already over!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(
                        request_message=message_types.VoidMessage,
                        response_message=UserForms,
                        path='/high_wins',
                        name='get_high_wins',
                        http_method='GET'
                        )
    def get_high_wins(self, request):
        """Get user's win ranking"""
        users = User.query().order(-User.wins)
        if not users:
            raise endpoints.NotFoundException('Cannot find any user!')
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(
                        request_message=message_types.VoidMessage,
                        response_message=UserForms,
                        path='/user_ranking',
                        name='get_user_ranking',
                        http_method='GET'
                        )
    def get_user_ranking(self, request):
        """Get user win rate ranking"""
        users = User.query(User.total_played > 0).fetch()
        if not users:
            raise endpoints.NotFoundException('Cannot find any user!')
        users = sorted(users, key=lambda x: x.win_percentage, reverse=True)
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(
                        request_message=GET_GAME_REQUEST,
                        response_message=GameHistory,
                        path='/game/{urlsafe_game_key}/history',
                        name='get_game_history',
                        http_method='GET'
                        )
    def get_game_history(self, request):
        """Return user's move history for the game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return GameHistory(move=str(game.move_histories))
        else:
            raise endpoints.NotFoundException('Game not Found!')


api = endpoints.api_server([HangmanApi])
