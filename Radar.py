import math
import sys
import pygame
import serial
import serial.tools.list_ports

# ---------------------------
# CONFIGURATION
# ---------------------------
PORT = "/dev/ttyACM0"      # Change if needed
BAUDRATE = 9600

# 3.5 inch Raspberry Pi display resolution
WIDTH, HEIGHT = 480, 320
FPS = 30  # Lower FPS for RPi performance

# Colors (RGB)
GREEN = (0, 255, 0)
GREEN_LINE = (100, 255, 100)
GREEN_TEXT = (150, 255, 150)
RED = (255, 60, 60)
BLACK = (0, 0, 0)
BG_COLOR = (10, 10, 10)

# Radar center for 3.5" display
RADAR_CX = 240  # Center horizontally
RADAR_CY = 210  # Position for 180° display
RADAR_RADIUS = 200  # Maximum radar range

# ---------------------------
# SERIAL SETUP
# ---------------------------
def open_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=0.01)
        return ser
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None

ser = open_serial(PORT, BAUDRATE)

# Buffer for accumulating serial text
serial_buffer = ""

# These replicate your Processing variables
angle_str = ""
distance_str = ""
data_str = ""
no_object = ""
pix_distance = 0.0
i_angle = 0
i_distance = 0

# ---------------------------
# PYGAME SETUP
# ---------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar - Pygame Version")
clock = pygame.time.Clock()

# Fonts optimized for 3.5" screen
font_small = pygame.font.SysFont("consolas", 10)
font_medium = pygame.font.SysFont("consolas", 12)
font_large = pygame.font.SysFont("consolas", 14)

# A separate surface to simulate the fade / motion blur
# We draw radar stuff on this surface, then blit to the screen
radar_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
radar_surface.fill((*BG_COLOR, 255))  # dark background


# ---------------------------
# UTILITY FUNCTIONS
# ---------------------------

def processing_to_screen(x_local, y_local):
    """
    Convert Processing-like coordinates (0,0 at radar center,
    positive y up) to Pygame screen coordinates (0,0 top-left,
    positive y down).
    """
    # Processing radar local: (0,0) at center, y up
    # We want: (RADAR_CX, RADAR_CY) is that center, y down.
    x_screen = RADAR_CX + x_local
    y_screen = RADAR_CY - y_local
    return (int(x_screen), int(y_screen))

def draw_radar(surface):
    # Arcs: Processing arcs were:
    # arc(0,0,1800,1800,PI,TWO_PI); etc.
    # That’s radius 900, 700, 500, 300
    pygame.draw.arc(
        surface, GREEN,
        (RADAR_CX - 900, RADAR_CY - 900, 1800, 1800),
        math.pi, 2 * math.pi, 2
    )
    pygame.draw.arc(
        surface, GREEN,
        (RADAR_CX - 700, RADAR_CY - 700, 1400, 1400),
        math.pi, 2 * math.pi, 2
    )
    pygame.draw.arc(
        surface, GREEN,
        (RADAR_CX - 500, RADAR_CY - 500, 1000, 1000),
        math.pi, 2 * math.pi, 2
    )
    pygame.draw.arc(
        surface, GREEN,
        (RADAR_CX - 300, RADAR_CY - 300, 600, 600),
        math.pi, 2 * math.pi, 2
    )

    # Horizontal axis (0-180 degree line)
    start = processing_to_screen(-RADAR_RADIUS, 0)
    end = processing_to_screen(RADAR_RADIUS, 0)
    pygame.draw.line(surface, GREEN, start, end, 1)

    # Angle guide lines at 30, 60, 90, 120, 150 degrees
    for deg in (30, 60, 90, 120, 150):
        rad = math.radians(deg)
        x = RADAR_RADIUS * math.cos(rad)
        y = RADAR_RADIUS * math.sin(rad)
        start = processing_to_screen(0, 0)
        end = processing_to_screen(x, y)
        pygame.draw.line(surface, GREEN, start, end, 1)


def draw_object(surface):
    global pix_distance, i_angle, i_distance
    # Only if distance < 40 cm
    if i_distance < 40:
        pix_distance = i_distance * 5  # Scale factor for 3.5" display (200px/40cm = 5)
        rad = math.radians(i_angle)

        # Draw red line from detected object to edge
        x1 = pix_distance * math.cos(rad)
        y1 = pix_distance * math.sin(rad)
        x2 = RADAR_RADIUS * math.cos(rad)
        y2 = RADAR_RADIUS * math.sin(rad)

        start = processing_to_screen(x1, y1)
        end = processing_to_screen(x2, y2)
        pygame.draw.line(surface, RED, start, end, 3)
        
        # Draw a circle at the detected object position
        obj_pos = processing_to_screen(x1, y1)
        pygame.draw.circle(surface, RED, obj_pos, 3)


def draw_line(surface):
    global i_angle
    # Sweep line showing current scanning angle
    rad = math.radians(i_angle)
    x2 = RADAR_RADIUS * math.cos(rad)
    y2 = RADAR_RADIUS * math.sin(rad)

    start = processing_to_screen(0, 0)
    end = processing_to_screen(x2, y2)
    pygame.draw.line(surface, GREEN_LINE, start, end, 2)


def draw_text(surface):
    global i_distance, i_angle, no_object

    if i_distance > 40:
        no_object = "Out"
    else:
        no_object = "In"

    # Bottom status bar
    pygame.draw.rect(surface, BLACK, (0, 235, WIDTH, HEIGHT - 235))
    pygame.draw.line(surface, GREEN, (0, 235), (WIDTH, 235), 1)

    # Distance scale labels - only show key distances
    scale_y = RADAR_CY + 5
    for dist_cm in [10, 20, 30, 40]:
        x_pos = RADAR_CX + (dist_cm * 5)  # 5 pixels per cm
        if x_pos < WIDTH - 20:  # Only draw if within screen
            txt = font_small.render(f"{dist_cm}", True, GREEN_TEXT)
            surface.blit(txt, (x_pos - 5, scale_y))
            pygame.draw.line(surface, GREEN, (x_pos, RADAR_CY - 3), (x_pos, RADAR_CY + 3), 1)

    # Compact title
    txt_title = font_medium.render("RADAR", True, GREEN_LINE)
    surface.blit(txt_title, (5, 5))
    
    # Status info - compact layout
    info_y = 240
    txt_status = font_small.render(f"{no_object}", True, GREEN_TEXT if i_distance > 40 else RED)
    txt_ang = font_small.render(f"A:{i_angle:03d}°", True, GREEN_TEXT)
    
    surface.blit(txt_status, (5, info_y))
    surface.blit(txt_ang, (5, info_y + 15))

    if i_distance < 40:
        txt_dist = font_small.render(f"D:{i_distance}cm", True, RED)
    else:
        txt_dist = font_small.render("D:---", True, GREEN_TEXT)
    surface.blit(txt_dist, (5, info_y + 30))

    # Degree labels - only key angles
    for deg in [0, 45, 90, 135, 180]:
        rad = math.radians(deg)
        label_dist = RADAR_RADIUS + 15
        x = label_dist * math.cos(rad)
        y = label_dist * math.sin(rad)
        screen_pos = processing_to_screen(x, y)
        
        text_surface = font_small.render(f"{deg}", True, GREEN_LINE)
        text_rect = text_surface.get_rect(center=screen_pos)
        surface.blit(text_surface, text_rect)


def read_serial():
    """
    Rough equivalent of Processing's serialEvent: reads until '.' and
    parses "angle,distance." into i_angle and i_distance.
    """
    global ser, serial_buffer, angle_str, distance_str, data_str, i_angle, i_distance

    if ser is None or not ser.is_open:
        return

    try:
        bytes_available = ser.in_waiting
    except OSError:
        return

    if bytes_available > 0:
        try:
            chunk = ser.read(bytes_available).decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            return

        serial_buffer += chunk

        # Process all complete messages ending with '.'
        while '.' in serial_buffer:
            msg, serial_buffer = serial_buffer.split('.', 1)
            # msg should be "angle,distance"
            if ',' in msg:
                angle_str, distance_str = msg.split(',', 1)
                try:
                    i_angle = int(angle_str.strip())
                    i_distance = int(distance_str.strip())
                except ValueError:
                    pass


# ---------------------------
# MAIN LOOP
# ---------------------------
running = True
while running:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Read serial data
    read_serial()

    # Simulate motion blur with fade effect
    fade_rect = pygame.Surface((WIDTH, 235), pygame.SRCALPHA)
    fade_rect.fill((*BG_COLOR, 10))  # Low alpha for smooth fade trail
    radar_surface.blit(fade_rect, (0, 0))

    # Draw radar, line, object, text on radar_surface
    draw_radar(radar_surface)
    draw_line(radar_surface)
    draw_object(radar_surface)
    draw_text(radar_surface)

    # Blit full radar_surface to main screen
    screen.blit(radar_surface, (0, 0))

    # Flip display
    pygame.display.flip()

# Cleanup
if ser is not None and ser.is_open:
    ser.close()
pygame.quit()
sys.exit()