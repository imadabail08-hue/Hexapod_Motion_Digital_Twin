import pygame
from collections import deque

class GraphWidget:
    def __init__(self, rect: tuple, title: str, max_points: int = 150, min_val: float = -45.0, max_val: float = 45.0):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.max_points = max_points
        self.min_val = min_val
        self.max_val = max_val
        self.pitch_history = deque(maxlen=max_points)
        self.roll_history = deque(maxlen=max_points)
        self.servo_history = deque(maxlen=max_points)

    def add_point(self, pitch: float, roll: float, servo: float):
        self.pitch_history.append(pitch)
        self.roll_history.append(roll)
        self.servo_history.append(servo)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        # Background & border
        pygame.draw.rect(surface, (25, 25, 25), self.rect)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, width=1)

        # Title
        t_surf = font.render(self.title, True, (160, 160, 160))
        surface.blit(t_surf, (self.rect.x + 8, self.rect.y + 6))

        # Center line (0 deg)
        zero_y = self.rect.y + self.rect.height // 2
        pygame.draw.line(surface, (40, 40, 40), (self.rect.x, zero_y), (self.rect.right, zero_y))

        # Draw lines
        def val_to_y(v: float) -> int:
            norm = (v - self.min_val) / (self.max_val - self.min_val)
            norm = max(0.0, min(1.0, norm))
            return int(self.rect.bottom - norm * self.rect.height)

        dx = self.rect.width / max(1, self.max_points)

        # Pitch (cyan)
        if len(self.pitch_history) > 1:
            pts = [(int(self.rect.x + i * dx), val_to_y(val)) for i, val in enumerate(self.pitch_history)]
            pygame.draw.lines(surface, (0, 188, 212), False, pts, 2)

        # Roll (green)
        if len(self.roll_history) > 1:
            pts = [(int(self.rect.x + i * dx), val_to_y(val)) for i, val in enumerate(self.roll_history)]
            pygame.draw.lines(surface, (76, 175, 80), False, pts, 2)
