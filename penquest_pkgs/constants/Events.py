class Events:
    """Contains contstants for 
    """

    # Control events
    CONNECTION_ID_RECEIVED      = 'connection_id_received'

    # Change events
    GAME_PHASE_CHANGED          = 'game_phase_changed'              # Received changes to the game phase (shopping, attacker, defender)
    GAME_STORAGE_PHASE_CHANGED  = 'game_storage_phase_changed'      # Received changes to the game storage phase (lobby, running, ended)
    LOBBY_CHANGED               = 'lobby_changed'                   # Received changes to the lobby info
    SCENARIO_CHANGED            = 'scenario_changed'                # Received changes to the scenario
    BOARD_CHANGED               = 'board_changed'                   # Received changes to assets on the board
    SELECTION_OFFER_CHANGED     = 'selection_offer_changed'         # Received changes to the selection offer (like drawing cards)
    HAND_CHANGED                = 'hand_changed'                    # Received changes to the cards in the hand
    SHOP_CHANGED                = 'shop_changed'                    # Received changes to the shop
    EQUIPMENT_CHANGED           = 'equipment_changed'               # Received changes to the equipment of the player
    PLAYERS_CHANGED             = 'players_changed'                 # Received changes to the players in the game
    PLAYER_ROLE_CHANGED         = 'player_role_changed'             # Received changes to the player role this event informs the client of the roles of all players
    PLAYER_ATTRIBUTE_CHANGED    = 'player_attribute_changed'        # Received changes to the player attributes
    GAME_OPTIONS_CHANGED        = 'game_options_changed'            # Received changes to the game options made by the host

    # Info events
    GAME_STARTED                = 'game_started'                    # Received when the game has started
    GAME_ENDED                  = 'game_ended'                      # Received when the game has ended

    # Action events
    GET_SHOPPING_LIST           = 'get_shopping_list'               # Send when the player needs to select equipment to buy
    GET_SELECT_ACTION           = 'get_select_action'               # Send when the player needs to select an action to play
    ALL_ACTIONS_PLAYABLE        = 'all_actions_playable'            # Send when the gameserver replyed to the GET_VALID_ACTIONS command
    SEND                        = 'send'                            # Indicates that a message should be send to the gameserver

    # Command reply events
    PLAY_ACTION_REPLY           = 'play_action_reply'               # Received when the gameserver replyed to the PLAY_ACTION command
    GAME_LEFT                   = 'game_left'                       # Received after4 a LEAVE GAME command was sent
