import pygame

class ImuDisplayWidget:
    def __init__(self, rect: tuple):
        self.rect = pygame.Rect(rect)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, state: dict):
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, width=1)

        imu = state.get("imu", {}).get("raw", {})
        orient = state.get("orientation", {})

        x = self.rect.x + 12
        y = self.rect.y + 10

        t = font.render("IMU TELEMETRY & ATTITUDE", True, (0, 188, 212))
        surface.blit(t, (x, y))
        y += 24

        p = orient.get("pitch", 0.0)
        r = orient.get("roll", 0.0)
        yw = orient.get("yaw", 0.0)

        # RPY
        rpy_text = f"PITCH: {p:+.1f}°   ROLL: {r:+.1f}°   YAW: {yw:+.1f}°"
        rpy_surf = font.render(rpy_text, True, (240, 240, 240))
        surface.blit(rpy_surf, (x, y))
        y += 20

        # Accel
        ax = imu.get("ax", 0.0)
        ay = imu.get("ay", 0.0)
        az = imu.get("az", 0.0)
        acc_text = f"ACCEL (m/s²):  X={ax:+.2f}  Y={ay:+.2f}  Z={az:+.2f}"
        surface.blit(font.render(acc_text, True, (180, 180, 180)), (x, y))
        y += 20

        # Gyro
        gx = imu.get("gx", 0.0)
        gy = imu.get("gy", 0.0)
        gz = imu.get("gz", 0.0)
        gyro_text = f"GYRO (°/s):    X={gx:+.1f}  Y={gy:+.1f}  Z={gz:+.1f}"
        surface.blit(font.render(gyro_text, True, (180, 180, 180)), (x, y))
