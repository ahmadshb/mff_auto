import re
from lib.functions import wait_until, is_strings_similar, r_sleep
from lib.game import ui
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
import lib.logger as logging
logger = logging.get_logger(__name__)

cur_slash_max_regexp = re.compile(r"(\d*) ?/ ?(\d*)")


class GameMode:
    """Class for working with game modes."""

    def __init__(self, name, stages=0, max_stages=0, ui_button=None, ui_board=None):
        self.name = name
        self.stages = stages
        self.max_stages = max_stages
        self.ui_button = ui_button
        self.ui_board = ui_board


class Game:
    """Class for working with main game methods."""

    ACQUIRE_HEROIC_QUEST_REWARDS = False

    def __init__(self, player, user_name=None):
        """Class initialization.

        :param lib.player.NoxWindow player: instance of game player.
        :param user_name: game user name.
        """
        self.player = player
        self.player.click_button = self.do_after_loading_circle_decorator(self.player.click_button)
        self.player.is_ui_element_on_screen = self.do_after_loading_circle_decorator(
            self.player.is_ui_element_on_screen)
        self.player.is_image_on_screen = self.do_after_loading_circle_decorator(self.player.is_image_on_screen)
        self.ui = ui.load_ui_settings()
        self._mode_names = ui.load_game_modes()
        self._user_name = user_name
        self.timeline_team = 1
        self.mission_team = 1
        self._modes = {}

    def do_after_loading_circle_decorator(self, func):
        """player.click_button decorator."""
        def wrapped(*args, **kwargs):
            if self.is_loading_circle():
                r_sleep(1)
            return func(*args, **kwargs)
        return wrapped

    @staticmethod
    def get_current_and_max_values_from_text(text, regexp=cur_slash_max_regexp):
        """Get current and max value from text by regular expression."""
        result = re.findall(pattern=regexp, string=text)
        logger.debug(f"Getting current and max value: {result} from text: {text}")
        try:
            current_value = 0 if not result else int(result[0][0])
            max_value = 0 if not result else int(result[0][1])
        except ValueError:
            current_value = 0
            max_value = 0
        return current_value, max_value

    @property
    def user_name(self):
        """Player's username."""
        if not self._user_name:
            self.go_to_main_menu()
            self.ui['USER_NAME'].scale = 3
            self._user_name = self.player.get_screen_text(self.ui['USER_NAME'])
            logger.debug(f"Username: {self._user_name}")
        return self._user_name

    @property
    def energy(self):
        """Game energy bar's value."""
        energy = self.player.get_screen_text(self.ui['ENERGY'])
        current_energy, _ = self.get_current_and_max_values_from_text(energy)
        return current_energy

    @property
    def energy_max(self):
        """Max value of energy."""
        energy = self.player.get_screen_text(self.ui['ENERGY'])
        _, energy_max = self.get_current_and_max_values_from_text(energy)
        return energy_max

    @property
    def gold(self):
        """Game's gold value."""
        return self.player.get_screen_text(self.ui['GOLD']).replace(",", "")

    @property
    def boost(self):
        """Game boost points' value."""
        return self.player.get_screen_text(self.ui['BOOST'])

    def get_all_modes(self):
        """Get information about all game modes."""
        self.find_mode_on_content_status_board("ALL")

    def get_mode(self, name):
        """Get game mode by name."""
        if not self._modes or name not in self._modes:
            self.find_mode_on_content_status_board(mode_name=name)
            for empty_mode_name in [m_name for m_name in self._mode_names if m_name not in self._modes]:
                self._modes[empty_mode_name] = GameMode(name=empty_mode_name)
        return self._modes[name]

    def clear_modes(self):
        """Clear all game modes information."""
        self._modes = {}

    def set_timeline_team(self, team_number):
        """Set team for Timeline Battles."""
        if team_number < 1 or team_number > 5:
            logger.error("Timeline team: Team number should be between 1 and 5.")
        else:
            self.timeline_team = team_number

    def set_mission_team(self, team_number):
        """Set team for usual missions."""
        if team_number < 1 or team_number > 5:
            logger.error("Mission team: Team number should be between 1 and 5.")
        else:
            self.mission_team = team_number

    def is_main_menu(self):
        """Check if is current screen is main menu."""
        return self.player.is_ui_element_on_screen(self.ui['TEAM']) and self.player.is_ui_element_on_screen(
            self.ui['STORE'])

    def is_loading_circle(self):
        """Check if loading circle is on screen."""
        loading_circle_rects = [self.ui['LOADING_CIRCLE_1'].rect, self.ui['LOADING_CIRCLE_2'].rect,
                                self.ui['LOADING_CIRCLE_3'].rect, self.ui['LOADING_CIRCLE_4'].rect,
                                self.ui['LOADING_CIRCLE_5'].rect, self.ui['LOADING_CIRCLE_6'].rect,
                                self.ui['LOADING_CIRCLE_7'].rect, self.ui['LOADING_CIRCLE_8'].rect]
        loading_color = self.ui['LOADING_CIRCLE_1'].button
        result = self.player.is_color_similar(color=(loading_color[0], loading_color[1], loading_color[2]),
                                              rects=loading_circle_rects)
        if result:
            logger.debug("Loading circle is on screen.")
        return result

    def go_to_main_menu(self):
        """Go to main menu screen."""
        if not self.is_main_menu():
            self.player.click_button(self.ui['HOME'].button)
            self.close_ads()

    def go_to_content_status_board(self):
        """Go to Content Status Board screen."""
        self.go_to_main_menu()
        if wait_until(self.is_main_menu, timeout=3):
            self.player.click_button(self.ui['CONTENT_STATUS_BOARD_BUTTON'].button)
            return wait_until(self.player.is_ui_element_on_screen, timeout=3,
                              ui_element=self.ui['CONTENT_STATUS_BOARD_LABEL'])

    def find_mode_on_content_status_board(self, mode_name):
        """Find game mode on Content Status Board.

        :param mode_name: mode's name.

        :return: GameMode: class representation of found game mode.
        """
        self.go_to_content_status_board()
        mode_from_board_1 = self.find_mode_on_board(mode_name=mode_name, board=self.ui['CONTENT_STATUS_BOARD_1'],
                                                    element=self.ui['CONTENT_STATUS_ELEMENT_1'], rows=3, cols=4)
        if mode_from_board_1:
            return mode_from_board_1
        else:
            self.player.drag(self.ui['CONTENT_STATUS_DRAG_FROM'].button, self.ui['CONTENT_STATUS_DRAG_TO'].button,
                             duration=0.2)
            r_sleep(1)
            return self.find_mode_on_board(mode_name=mode_name, board=self.ui['CONTENT_STATUS_BOARD_2'],
                                           element=self.ui['CONTENT_STATUS_ELEMENT_1'], rows=3, cols=4)

    def find_mode_on_board(self, mode_name, board, element, rows, cols):
        """Parse information from Content Status Board screen about game modes.
        Screen contains table of game modes with additional info.

        :param mode_name: mode's name.
        :param board: rectangle of Content Status Board.
        :param element: template of rectangle of game mode element. Contains only width/height information.
        :param rows: rows count of board's table.
        :param cols: cols count of board's table.

        :return: dictionary with information about game modes on board.
        """

        def chunk_items(items, chunk_size):
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                yield chunk

        offset = element.button
        elements = [(board.rect, ui.Rect(i * element.rect.width + i * offset.width,
                                         j * element.rect.height + j * offset.height,
                                         (i + 1) * element.rect.width + i * offset.width,
                                         (j + 1) * element.rect.height + j * offset.height))
                    for j in range(cols) for i in range(rows)]
        for chunk_element in chunk_items(items=elements, chunk_size=cpu_count()):
            pool = ThreadPool()
            modes = pool.starmap(self.get_mode_from_element, chunk_element)
            for mode in [non_empty_mode for non_empty_mode in modes if non_empty_mode]:
                self._modes[mode.name] = mode
                if mode.name == mode_name:
                    return mode

    def get_mode_from_element(self, board_rect, element_rect):
        """Get information about game mode from single game mode element.

        :param board_rect: rectangle of Content Status Board.
        :param element_rect: rectangle of single game mode element inside board.

        :return: dictionary with information about game mode inside element_rect.
        """
        # Getting global rects of elements
        element_ui = ui.UIElement('UI_BOARD_ELEMENT', text_rect=element_rect)
        element_ui.rect.parent = board_rect
        self.ui['CONTENT_STATUS_ELEMENT_LABEL'].rect.parent = element_ui.rect
        self.ui['CONTENT_STATUS_ELEMENT_STAGE'].rect.parent = element_ui.rect
        self.ui['CONTENT_STATUS_ELEMENT_COMPLETE'].rect.parent = element_ui.rect
        self.ui['CONTENT_STATUS_ELEMENT_LABEL'].scale = 3
        self.ui['CONTENT_STATUS_ELEMENT_STAGE'].scale = 3
        # Getting board image and element image. Use it for stage recognize
        board_image = self.player.get_screen_image(board_rect.value)
        element_image = self.player.get_image_from_image(board_image, element_ui)
        stage_label_image = self.player.get_image_from_image(element_image,
                                                             self.ui['CONTENT_STATUS_ELEMENT_LABEL'])
        stage_label = self.player.get_screen_text(self.ui['CONTENT_STATUS_ELEMENT_LABEL'], screen=stage_label_image)
        logger.debug(f"Stage found: {stage_label}")
        stage_completion_screen = self.player.get_image_from_image(element_image,
                                                                   self.ui['CONTENT_STATUS_ELEMENT_COMPLETE'])
        if self.player.is_ui_element_on_screen(self.ui['CONTENT_STATUS_ELEMENT_COMPLETE'],
                                               screen=stage_completion_screen):
            current_stages, max_stages = 0, 0
        else:
            stage_counter_image = self.player.get_image_from_image(element_image,
                                                                   self.ui['CONTENT_STATUS_ELEMENT_STAGE'])
            stage_counter_text = self.player.get_screen_text(self.ui['CONTENT_STATUS_ELEMENT_STAGE'],
                                                             screen=stage_counter_image)
            logger.debug(f"Stage: {stage_label}; stages: {stage_counter_text}")
            current_stages, max_stages = self.get_current_and_max_values_from_text(stage_counter_text)
        # Find mode and return info about stages and board
        for mode_name in self._mode_names:
            if is_strings_similar(mode_name, stage_label):
                game_mode = GameMode(name=mode_name, stages=current_stages, max_stages=max_stages,
                                     ui_button=element_ui.rect.global_rect, ui_board=board_rect.value)
                return game_mode

    def select_mode(self, name):
        """Select and open game mode from Content Status Board.

        :param name: game mode's name.
        """
        self.go_to_content_status_board()
        mode = self._modes[name]
        if mode.ui_board == self.ui['CONTENT_STATUS_BOARD_2'].rect.value:
            logger.debug(f"Mode {name} is on second board. Dragging")
            self.player.drag(self.ui['CONTENT_STATUS_DRAG_FROM'].button, self.ui['CONTENT_STATUS_DRAG_TO'].button,
                             duration=0.4)
            r_sleep(1)
        self.player.click_button(mode.ui_button)

    def go_to_mission_selection(self):
        """DEPRECATED.

        Go to Missions screen.
        """
        self.go_to_main_menu()
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['ENTER_MISSIONS']):
            self.player.click_button(self.ui['ENTER_MISSIONS'].button)
            r_sleep(1)

    def go_to_challenge_selection(self):
        """DEPRECATED.

        Go to Challenges screen.
        """
        self.go_to_main_menu()
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['ENTER_MISSIONS']):
            self.player.click_button(self.ui['ENTER_MISSIONS'].button)
            r_sleep(1)
            self.player.click_button(self.ui['CHALLENGE_MISSIONS'].button)
            r_sleep(1)

    def go_to_arena(self):
        """DEPRECATED.

        Go to Arena screen.
        """
        self.go_to_main_menu()
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['ENTER_MISSIONS']):
            self.player.click_button(self.ui['ENTER_MISSIONS'].button)
            r_sleep(1)
            self.player.click_button(self.ui['ARENA_MISSIONS'].button)
            r_sleep(1)

    def go_to_coop(self):
        """Go to Co-op screen."""
        self.go_to_main_menu()
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['ENTER_MISSIONS']):
            self.player.click_button(self.ui['ENTER_MISSIONS'].button)
            if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['COOP_MISSIONS']):
                self.player.click_button(self.ui['COOP_MISSIONS'].button)

    def go_to_challenges(self):
        """Go to Challenges screen."""
        self.go_to_main_menu()
        self.player.click_button(self.ui['MAIN_MENU'].button)
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['MAIN_MENU']):
            if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['MAIN_MENU_CHALLENGES']):
                self.player.click_button(self.ui['MAIN_MENU_CHALLENGES'].button)
                return wait_until(self.player.is_ui_element_on_screen, timeout=3,
                                  ui_element=self.ui['CHALLENGES_STAGE_LABEL'])
            logger.warning("Can't find Challenges button in Main menu, exiting")
            self.player.click_button(self.ui['MAIN_MENU'].button)
        return False

    def go_to_lab(self):
        """Go to Lab screen."""
        self.go_to_main_menu()
        self.player.click_button(self.ui['MAIN_MENU'].button)
        if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['MAIN_MENU']):
            if wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['MAIN_MENU_LAB']):
                self.player.click_button(self.ui['MAIN_MENU_LAB'].button)
                return wait_until(self.player.is_ui_element_on_screen, timeout=3,
                                  ui_element=self.ui['LAB_LABEL'])
            logger.warning("Can't find Lab button in Main menu, exiting")
            self.player.click_button(self.ui['MAIN_MENU'].button)
        return False

    def restart_game(self):
        """Restart game.

        :return: True or Flase: was restart successful.
        """
        if self.close_game():
            return self.start_game()
        logger.warning("Failed to restart game")
        return False

    def close_game(self):
        """Close game.

        :return: True or False: was game closed.
        """
        self.player.press_key("{PGUP}", True)
        if not wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['GAME_TASK']):
            logger.error("Failed to minimize game task.")
        self.player.drag(self.ui['GAME_TASK_DRAG_FROM'].button, self.ui['GAME_TASK_DRAG_TO'].button, duration=0.4)
        return wait_until(self.player.is_ui_element_on_screen, timeout=3, ui_element=self.ui['GAME_APP'])

    def start_game(self):
        """Start game.

        :return: True or False: was game started.
        """
        def is_game_started():
            is_started = self.close_maintenance_notice() or self.close_ads() or self.is_main_menu()
            if not is_started and self.player.is_ui_element_on_screen(self.ui['NEWS_ON_START_GAME']):
                self.player.click_button(self.ui['NEWS_ON_START_GAME'].button)
            return is_started

        self.player.click_button(self.ui['GAME_APP'].button)
        if wait_until(is_game_started, timeout=60):
            self.close_maintenance_notice()
            self.close_ads()
            return True
        logger.warning("Failed to start game")
        return False

    def close_maintenance_notice(self):
        """Close maintenance notice window."""
        if self.player.is_ui_element_on_screen(ui_element=self.ui['MAINTENANCE_NOTICE']):
            self.player.click_button(self.ui['MAINTENANCE_NOTICE'].button)
            return True
        return False

    def close_ads(self, timeout=2):
        """Close any ads on main menu screen.

        :param timeout: timeout of waiting for ads.

        :return: True or False: were ads closed.
        """
        def close_ad(ad_ui):
            if self.player.is_ui_element_on_screen(ad_ui):
                self.player.click_button(ad_ui.button)
                if wait_until(self.player.is_ui_element_on_screen, timeout=1.5,
                              ui_element=self.ui['MAIN_MENU_AD_CLOSE']):
                    self.player.click_button(self.ui['MAIN_MENU_AD_CLOSE'].button)
                    return True
            return False

        def close_ads():
            return close_ad(self.ui['MAIN_MENU_AD']) or \
                   close_ad(self.ui['MAIN_MENU_AD_2']) or \
                   close_ad(self.ui['MAIN_MENU_AD_3'])

        result = False
        for _ in range(timeout):
            result = result or wait_until(close_ads, timeout=1)
        return result
