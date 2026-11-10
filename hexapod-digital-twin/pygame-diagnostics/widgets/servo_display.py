import pygame

class ServoDisplayWidget:
    def __init__(self, rect: tuple):
        self.rect = pygame.Rect(rect)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, state: dict):
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, width=1)

        ps = state.get("physicalServo", {})
        angle = ps.get("angle", 90)
        cmd = ps.get("command", 90)

        x = self.rect.x + 12
        y = self.rect.y + 10

        t = font.render("PHYSICAL SERVO (MG90S)", True, (255, 152, 0))
        surface.blit(t, (x, y))
        y += 24

        surface.blit(font.render(f"CURRENT ANGLE: {angle}°   COMMAND: {cmd}°", True, (220, 220, 220)), (x, y))
        y += 24

        # Bar
        bar_w = self.rect.width - 24
        bar_h = 12
        pygame.draw.rect(surface, (15, 15, 15), (x, y, bar_w, bar_h))
        norm = (angle - 50) / (130 - 50)
        norm = max(0.0, min(1.0, norm))
        fill_w = int(norm * bar_w)
        pygame.draw.rect(surface, (255, 87, 34), (x, y, fill_w, bar_h))
        pygame.draw.rect(surface, (80, 80, 80), (x, y, bar_w, bar_h), width=1)
