import pygame
from typing import Callable, Optional

class ButtonWidget:
    def __init__(self, rect: tuple, text: str, callback: Callable[[], None], color=(50, 50, 50), text_color=(240, 240, 240)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.hovered = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        col = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30)) if self.hovered else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=4)
        pygame.draw.rect(surface, (80, 80, 80), self.rect, width=1, border_radius=4)

        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
