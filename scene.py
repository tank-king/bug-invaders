import traceback

from objects import *
from subtitles import SubtitleManager, BlinkingSubtitle, get_typed_subtitles
from transition import TransitionManager
from ui import *


def update_error_handle(f):
    def wrapper(obj: 'Scene', events: list[pygame.event.Event], *args, **kwargs):
        try:
            f(obj, events, *args, **kwargs)
        except Exception as e:
            obj.raise_error(e)
            print(e)
        if obj.error:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_e:
                        obj.show_traceback = not obj.show_traceback
                    if e.key == pygame.K_KP_PLUS:
                        obj.error_size += 5
                    if e.key == pygame.K_KP_MINUS:
                        obj.error_size -= 5
                    obj.error_size = clamp(obj.error_size, 5, 50)

    return wrapper


def draw_error_handle(f):
    def wrapper(obj: 'Scene', surf: pygame.Surface, *args, **kwargs):
        try:
            f(obj, surf, *args, **kwargs)
        except Exception as e:
            obj.raise_error(e)
            print(e)
            print(*traceback.format_exception(type(e), e, e.__traceback__))
        if obj.error:
            e = obj.error
            errors = traceback.format_exception(type(e), e, e.__traceback__)
            a = [i.split('\n') for i in errors]
            b = []
            for i in a:
                for x in i:
                    if x:
                        b.append(x)
            errors = b
            surf.fill(BG_COlOR)
            if obj.show_traceback:
                y = 150
                for i in errors:
                    t = text(i, obj.error_size)
                    y += obj.error_size
                    surf.blit(t, (50, y))
            else:
                t = text('Error', 150)
                surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                t = text('Press E to show traceback', 25)
                surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150)))

    return wrapper


class MetaClass(type):
    def __new__(mcs, name, bases, namespaces):
        for attr, attr_val in namespaces.items():
            if attr == 'update':
                namespaces[attr] = update_error_handle(attr_val)
            elif attr == 'draw':
                namespaces[attr] = draw_error_handle(attr_val)
        return super().__new__(mcs, name, bases, namespaces)


class Scene(metaclass=MetaClass):
    """
    Base signature for all menus
    """

    def __init__(self, manager: 'SceneManager', name='menu'):
        self.manager = manager
        self.name = name
        self.error: Optional[Exception] = None
        self.show_traceback = False
        self.error_size = 25

    def raise_error(self, exception: Exception):
        self.error = exception

    def reset(self):
        self.__init__(self.manager, self.name)

    def update(self, events: list[pygame.event.Event]):
        pass

    def draw(self, surf: pygame.Surface):
        surf.fill(BG_COlOR)
        surf.blit(text(self.name), (50, 50))


class UnloadedScene(Scene):
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_COlOR)
        t = text('Unloaded Scene', 100)
        surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


class IntermissionOneHelpScene(Scene):
    def __init__(self, manager, name):
        super().__init__(manager, name)
        self.surf = pygame.display.get_surface()


class WaveOver(Scene):
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_COlOR)
        t = text('WAVE OVER', 100)
        surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


class Home(Scene):
    def __init__(self, manager, name):
        super().__init__(manager, name)
        self.y = 100
        self.options = ['play', 'scores', 'settings', 'quit']
        self.actions = [
            lambda: self.manager.switch_mode('game', reset=True, transition=True),
            None, None,
            lambda: sys.exit(0)
        ]
        self.selected = 0
        self.sheet = LoopingSpriteSheet(get_path('assets', 'images', 'minibug_sheet.png'), 1, 3, 3, scale=2)

    def update(self, events: list[pygame.event.Event]):
        self.y = 150 + math.sin(time.time() * 2) * 20
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    self.selected -= 1
                if e.key == pygame.K_DOWN:
                    self.selected += 1
                if e.key == pygame.K_RETURN:
                    if self.actions[self.selected] is not None:
                        try:
                            self.actions[self.selected]()
                        except Exception as e:
                            print(e)
                self.selected %= len(self.options)

    def draw(self, surf: pygame.Surface):
        t = text('BUG', 150, '#511309')
        surf.blit(t, t.get_rect(center=(WIDTH // 2, self.y)))
        t = text('INVADERS', 55, '#511309')
        surf.blit(t, t.get_rect(center=(WIDTH // 2 - 8, self.y + 100)))
        y = HEIGHT // 2
        for i in range(len(self.options)):
            if i == self.selected:
                t = text(f'- {self.options[i]} -', 55, '#511309')
            else:
                t = text(self.options[i], 55, '#511309')
            surf.blit(t, t.get_rect(center=(WIDTH // 2, y + ((math.sin(time.time() * 5) * 3) if i == self.selected else 0))))
            y += 75
        for i in (-2, -1, 0, 1, 2):
            self.sheet.draw(surf, WIDTH // 2 + i * 100, HEIGHT // 2 - 50 - 25)


class Game(Scene):
    WAVE_CONFIG = {}
    WAVE = 0

    def __init__(self, manager, name):
        super().__init__(manager, name)
        self.viewport = VIEWPORT_RECT
        self.objects_manager = ObjectManager()
        self.subtitles_manager = SubtitleManager()
        # for j in range(10):
        #     for i in range(100 + 100 * (j % 2), WIDTH, 200):
        #         self.objects_manager.add(Bug(i, -j * 100))
        self.bug_holes = []
        for i in range(100, WIDTH, 200):
            bug_hole = BugHole(i, 50 + 25)
            self.objects_manager.add(bug_hole)
            self.bug_holes.append(bug_hole)
        # for i in range(5):
        #     self.objects_manager.add(BugHole(WIDTH // 2, 100 * i))
        self.spawn_timer = Timer(1)
        self.player = self.objects_manager.player
        self.heart_img = load_image(get_path('assets', 'images', 'heart.png'), scale=4)
        self.timer = Timer(2)
        self.stage = 'game'
        # TODO disable manual resetting of levels
        self.intermission = 0
        # self.subtitles_manager.add_multiple(get_typed_subtitles('Yooo', 2))

    def set_stage(self, stage):
        self.stage = stage

    def update(self, events: list[pygame.event.Event]):
        self.objects_manager.update(events)
        self.subtitles_manager.update()
        # self.bug_holes = [i for i in self.bug_holes if i.alive]
        if not any([not i.done() for i in self.bug_holes]):
            self.manager.switch_mode('home')
        if self.stage == 'game':
            # if self.timer.tick:
            #     self.player.destroy()
            if self.spawn_timer.tick:
                for i in self.bug_holes:
                    i.spawn(Bug)
            if not self.player.alive and self.objects_manager.get_object_count(EntryAnimationObject) == 0:
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.player.lives = 0
                    # self.manager.switch_mode('home')
                    # TODO RESET GAME
                    for i in self.bug_holes:
                        i.pause()
                    self.player.is_playing = False
                    self.stage = 'destroy_anim_for_game_over'
                else:
                    self.stage = 'destroy_anim_for_intermission'
                    for i in self.bug_holes:
                        i.pause()
                    self.player.is_playing = False
        elif self.stage == 'destroy_anim_for_intermission':
            if self.objects_manager.get_object_count(Explosion) == 0:
                # wait for all particle effects to be done
                self.intermission += 1
                self.subtitles_manager.add_multiple(
                    get_typed_subtitles(f'INTERMISSION {self.intermission}',
                                        _time=0.5,
                                        callback=lambda: self.subtitles_manager.add(BlinkingSubtitle(f'INTERMISSION {self.intermission}', time=2, blink_timer=0.25,
                                                                                                     callback=lambda: self.set_stage('player_reset')), )
                                        ))
                self.stage = 'intermission_text'
        elif self.stage == 'intermission_text':
            pass
        elif self.stage == 'player_reset':
            if not self.subtitles_manager.subtitles:
                # self.manager.switch_mode('home', transition=True)
                self.stage = 'game'

                def f():
                    self.player.restart()
                    self.player.set_intermission_config(self.intermission)
                    for j in self.bug_holes:
                        j.resume()

                self.objects_manager.add(
                    EntryAnimationObject(self.player.x,
                                         self.player.y,
                                         ('#511309', 'black', '#55241b', '#45283c'),
                                         callback=f,
                                         diff=45,
                                         particles_per_line=15,
                                         rate=5,
                                         max_particle_size=7
                                         )
                )
                self.timer.reset()
        elif self.stage == 'destroy_anim_for_game_over':
            if self.objects_manager.get_object_count(Explosion) == 0:
                # wait for all particle effects to be done
                self.subtitles_manager.add_multiple(
                    get_typed_subtitles('Game OVER',
                                        _time=0.5,
                                        callback=lambda: self.subtitles_manager.add(BlinkingSubtitle('GAME OVER', time=2, blink_timer=0.25,
                                                                                                     callback=lambda: self.manager.switch_mode('home', transition=True)), )
                                        ))
                self.stage = 'game_over_text'
        elif self.stage == 'game_over_text':
            pass

    def draw(self, surf: pygame.Surface):
        self.objects_manager.draw(surf)
        rect = pygame.Rect(0, 0, WIDTH, 50)
        pygame.draw.rect(surf, '#511309', rect)
        pygame.draw.rect(surf, '#000000', rect, 5)
        t = text(self.player.score + 15000, 35, 'white', False)
        surf.blit(t, t.get_rect(centery=rect.centery - 2, right=rect.right - 10))
        for i in range(self.player.lives):
            x = i * (self.heart_img.get_width() + 10) + self.heart_img.get_width()
            surf.blit(self.heart_img, self.heart_img.get_rect(center=(x, rect.centery)))
        t = text('Wave 1', 35, 'white', False)
        surf.blit(t, t.get_rect(centerx=rect.centerx, centery=rect.centery - 2))
        self.subtitles_manager.draw(surf)


class SceneManager:
    def __init__(self):
        self.to_switch = 'none'  # to-switch transition
        self.to_reset = False
        self.to_save_in_stack = True
        self._transition_manager = TransitionManager()  # overall transition
        # self._objects_manager = ObjectManager()  # to be used across all menus
        self._subtitle_manager = SubtitleManager()  # overall subtitles
        # pre-set menus to be loaded initially
        self.menu_references = {
        }
        self.menu_references.clear()
        this = sys.modules[__name__]
        self.menu_references = {i.__name__.lower(): i for i in [getattr(this, j) for j in dir(this)] if isinstance(i, MetaClass)}
        self.menus = {}
        for i, _ in self.menu_references.items():
            self.menus[i] = self.menu_references.get(i)(self, i)
        self.mode = 'home'
        self.menu = self.menus[self.mode]
        self.mode_stack = []  # for stack based scene rendering
        self._default_reset = False
        self._default_transition = False

    def get_menu(self, menu):
        try:
            return self.menus[menu]
        except KeyError:
            return UnloadedScene(self, 'Error')

    def switch_to_prev_mode(self):
        try:
            self.switch_mode(self.mode_stack.pop(), self._default_reset, self._default_transition, save_in_stack=False)
        except IndexError:
            sys.exit(0)

    def switch_mode(self, mode, reset=False, transition=False, save_in_stack=False):
        if mode in self.menus:
            if transition:
                self.to_switch = mode
                self.to_reset = reset
                self.to_save_in_stack = save_in_stack
                self._transition_manager.close()
            else:
                if save_in_stack:
                    self.mode_stack.append(self.mode)
                self.mode = mode
                self.menu = self.menus[self.mode]
                if reset:
                    self.menu.reset()
                self._subtitle_manager.clear()

    def update(self, events: list[pygame.event.Event]):
        if self.to_switch != 'none':
            if self._transition_manager.transition.status == 'closed':
                self.switch_mode(self.to_switch, self.to_reset, transition=False, save_in_stack=self.to_save_in_stack)
                self.to_switch = 'none'
                self.to_reset = False
                self._transition_manager.open()
        self.menu.update(events)
        self._transition_manager.update(events)
        # self._objects_manager.update(events)
        self._subtitle_manager.update()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    self.menu.reset()
                if e.key == pygame.K_ESCAPE:
                    self.switch_to_prev_mode()
                if e.key == pygame.K_s:
                    if self.mode == 'game':
                        self.switch_mode('home', transition=True)
                    else:
                        self.switch_mode('game', transition=True)

    def draw(self, surf: pygame.Surface):
        self.menu.draw(surf)
        self._transition_manager.draw(surf)
        # self._objects_manager.draw(surf)
        self._subtitle_manager.draw(surf)
