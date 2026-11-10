import pygame

class StatusPanelWidget:
    def __init__(self, rect: tuple):
        self.rect = pygame.Rect(rect)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, state: dict):
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, width=1)

        conn = state.get("connection", {})
        esp32_ok = conn.get("esp32", False)
        webots_ok = conn.get("webots", False)
        estop = state.get("emergencyStop", False)
        mode = state.get("mode", "UNKNOWN")

        y = self.rect.y + 10
        x = self.rect.x + 12

        # Title
        t = font.render("SUBSYSTEM HEALTH", True, (0, 188, 212))
        surface.blit(t, (x, y))
        y += 24

        def draw_status(label: str, ok: bool, ok_str="ONLINE", fail_str="OFFLINE"):
            nonlocal y
            lbl = font.render(label, True, (160, 160, 160))
            surface.blit(lbl, (x, y))
            col = (76, 175, 80) if ok else (244, 67, 54)
            val = font.render(ok_str if ok else fail_str, True, col)
            surface.blit(val, (x + 120, y))
            y += 20

        draw_status("ESP32 GATEWAY", esp32_ok, "CONNECTED", "DISCONNECTED")
        draw_status("WEBOTS SIM", webots_ok, "RUNNING", "STOPPED")
        draw_status("SAFETY STATUS", not estop, "NORMAL", "ESTOP ACTIVE")

        y += 4
        m_lbl = font.render("ACTIVE MODE:", True, (160, 160, 160))
        surface.blit(m_lbl, (x, y))
        m_val = font.render(str(mode), True, (255, 152, 0))
        surface.blit(m_val, (x + 120, y))
