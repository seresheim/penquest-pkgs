class Commands:
    # Lobby Commands
    CREATE_NEW_GAME_LOBBY       = 'create_new_game_lobby'           # Creates a new lobby on the gameserver
    JOIN_LOBBY                  = 'join_lobby'                      # Joins an existing lobby
    SELECT_SCENARIO             = 'select_scenario'                 # Sends the id of the scenario to the gameserver to select in the current lobby
    SELECT_GOAL                 = 'select_scenario_goal'            # Sends the id of the goal to the gameserver to select in the current lobby
    SET_SEED                    = 'set_seed'                        # Sends the seed to the gameserver to set inside the lobby
    UPDATE_GAME_OPTIONS         = 'update_game_options'             # Sends a list of game options to the gameserver to set inside the lobby
    ADD_BOT                     = 'add_bot'                         # Sends the slot and bot type to the gameserver to add a bot to the lobby
    SET_PLAYER_READINESS        = 'player_ready'                    # Sends the readyness startus of the player, if all players are ready, the game will start
    CHANGE_SLOT                 = 'change_slot'
    

    # Game Commands
    SHOPPING_FINISHED           = 'shopping_finished'               # Sends a signal to the gameserver that the player is done shopping
    BUY_EQUIPMENT               = 'buy_equipment'   	            # Sends a list of equipment to buy to the gameserver
    SELECT_ACTIONS              = 'select_actions'                  # Sends a list of action ids that where chosen by the player during an selection event (like drawing cards)
    GET_VALID_ACTIONS           = 'get_valid_actions'            # Sends a list of actions to the gameserver and only returns the valid ones
    PLAY_ACTION                 = 'play_action'                     # Sends an action to the gameserver to play
    SURRENDER                   = 'game_surrender'                       # Sends a signal to the gameserver that the player surrenders

    # Both
    LEAVE_GAME                  = 'leave_game'