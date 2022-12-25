import time

from utils import *
import pygame


class BaseUI:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, pos):
        self.x, self.y = pos

    def update(self, events):
        pass

    def draw(self, surf):
        pass


class Button(BaseUI):
    def __init__(self, x=0, y=0, w=100, h=50, label='Button', action=None):
        super().__init__(x, y)
        self.w = w
        self.h = h
        self.action = action
        self.label = label
        self.text = text(self.label, 25, aliased=True)
        self.active_color = (204, 122, 68)
        self.active_color = 'gold'
        self.inactive_color = (182, 122, 87)
        self.inactive_color = 'white'
        self.is_active = False
        self.selected = False

    def __repr__(self):
        return f'Button(x={self.x}, y={self.y}, w={self.w}, h={self.h}, label=\'{self.label}\')'

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def select(self):
        self.selected = not self.selected
        if self.action is not None:
            self.action()

    def deselect(self):
        self.selected = False

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx, my):
            self.is_active = True
        else:
            self.is_active = False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.is_active:
                        self.select()

    def draw(self, surf):
        color = self.active_color if self.selected else self.inactive_color
        if self.selected or self.is_active:
            pygame.draw.rect(surf, color, (self.x, self.y, self.w, self.h), 2)
        pygame.draw.line(surf, self.active_color, (self.x, self.y + self.h - 2), (self.x + self.w, self.y + self.h - 2), 2)
        surf.blit(self.text, self.text.get_rect(center=self.rect.center))


class Label(BaseUI):
    def __init__(self, x=0, y=0, w=100, h=50, label='Label'):
        super().__init__(x, y)
        self.w = w
        self.h = h
        self.label = label
        self.text = text(self.label, size=25, aliased=True)
        self.color = (182, 122, 87)
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.is_active = False

    def update(self, events):
        pass

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (self.x, self.y, self.w, self.h))
        surf.blit(self.text, self.text.get_rect(center=self.rect.center))


class InputBox(BaseUI):
    def __init__(self, x=0, y=0, w=100, h=50, default='Type Here', initial_string='', label='none', extendable=True, numeric_only=False):
        super().__init__(x, y)
        self.w = w
        self.h = h
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.numeric_only = numeric_only
        self.active_color = (204, 122, 68)
        self.inactive_color = (182, 122, 87)
        self.label = label
        self.default = default
        self.extendable = extendable
        self.is_active = False
        self.is_hovered = False
        self.text = initial_string
        self.allowed_input = 'abcdefghijklmnopqrstuvwxyz1234567890' if not self.numeric_only else '1234567890'
        self.cursor_visible = True
        self.cursor_blink_timer = time.time()

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx, my):
            self.is_hovered = True
        else:
            self.is_hovered = False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.is_hovered:
                        self.is_active = True
                    else:
                        self.is_active = False
            if e.type == pygame.KEYDOWN:
                if self.is_active:
                    if e.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                    if not len(self.text) > self.w // 15 - 3:
                        if e.key == pygame.K_SPACE:
                            self.text += ' '
                        # elif e.key != pygame.KMOD_SHIFT and chr(e.key) in self.allowed_input:
                        #     self.text += chr(e.key).upper()
            if e.type == pygame.TEXTINPUT:
                if self.is_active:
                    if e.text.lower() in self.allowed_input:
                        if not len(self.text) > self.w // 15 - 3:
                            self.text += e.text

    def draw(self, surf):
        color = self.active_color if self.is_hovered or self.is_active else self.inactive_color
        if self.is_active:
            display_text = self.text
        else:
            display_text = self.text if self.text != '' else self.default
        if self.is_active:
            if time.time() - self.cursor_blink_timer > 0.5:
                self.cursor_blink_timer = time.time()
                self.cursor_visible = not self.cursor_visible
            if self.cursor_visible:
                display_text += '_'
            else:
                display_text += ' '
        t = text(display_text, 25, aliased=True)
        pygame.draw.rect(surf, color, self.rect)
        surf.blit(t, t.get_rect(center=self.rect.center))


class Link:
    def __init__(self, link, _text):
        self.link = link
        self.text = _text

    def on_click(self):
        try:
            import webbrowser
            try:
                webbrowser.open_new_tab(self.link)
            except webbrowser.Error:
                return
        except ImportError:
            return


class Text(BaseUI):
    def __init__(self, x, y, _text, size=25):
        super().__init__(x, y)
        self.text = text(_text, size)

    def update(self, events):
        pass

    def draw(self, surf):
        surf.blit(self.text, self.text.get_rect(center=(self.x, self.y)))


class LinkUI(BaseUI):
    def __init__(self, x, y, link, _text, ac=(217, 49, 128), ic='gold', vc='magenta'):
        super().__init__(x, y)
        self.link = Link(link, _text)
        self.text_ic = text(_text, 25, ic)
        self.text_ac = text(_text, 25, ac)
        self.active = False

    @property
    def rect(self):
        return self.text_ic.get_rect(center=(self.x, self.y))

    def update(self, events):
        self.active = False
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx, my):
            self.active = True
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.active:
                        self.link.on_click()

    def draw(self, surf):
        if self.active:
            surf.blit(self.text_ac, self.text_ac.get_rect(center=(self.x, self.y)))
        else:
            surf.blit(self.text_ic, self.text_ic.get_rect(center=(self.x, self.y)))

