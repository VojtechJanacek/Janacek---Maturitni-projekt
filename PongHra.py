import pygame
import sys
import sqlite3
import random
smer = 1

pygame.init()

# Nastavení rychlostí qwe qwe qwe qwe qwe qwe qwe qwe 
mic_speed_x = 8
mic_speed_y = 8
cpu_speed = 8
speed_multiplier = 1.1  # Faktor zrychlení míče
accelerate_ball = False  # Režim zrychlování míče
cpu_points, hrac_points = 0, 0

# Text pro skóre
score_font = pygame.font.Font(None, 100)
menu_font = pygame.font.Font(None, 60)

# Připojení k databázi
conn = sqlite3.connect("game_history.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_score INTEGER,
    cpu_score INTEGER
)
""")
conn.commit()

# Pohyb/animace CPU
def pohyb_cpu():
    pravdepodobnost_chyby = 0.08  # 8% šance, že CPU udělá chybu
    if random.random() < pravdepodobnost_chyby:
        return  # CPU se někdy nepohne

    max_cpu_speed = 8  # Omezení maximální rychlosti CPU
    rozdil = mic.centery - cpu.centery

    if rozdil > 10:  
        cpu.y += min(max_cpu_speed, abs(rozdil))  # CPU se nepohybuje okamžitě na míč
    elif rozdil < -10:
        cpu.y -= min(max_cpu_speed, abs(rozdil))

    if cpu.top <= 0:
        cpu.top = 0
    if cpu.bottom >= vyska_okna:
        cpu.bottom = vyska_okna

# Pohyb/animace míče
def kolize_mice():
    global mic_speed_x, mic_speed_y, cpu_points, hrac_points, hrac_speed, cpu_speed, hrac2_speed

    mic.x += mic_speed_x
    mic.y += mic_speed_y

    # Kolize s horním a dolním okrajem
    if mic.top <= 0 or mic.bottom >= vyska_okna:
        mic_speed_y *= -1

    # Kolize s pravým okrajem (bod pro CPU)
    if mic.right >= sirka_okna:
        cpu_points += 1
        mic_restart()

    # Kolize s levým okrajem (bod pro hráče)
    if mic.left <= 0:
        hrac_points += 1
        mic_restart()

    # Kolize s hráčem
    if mic.colliderect(hrac):
        mic_speed_x *= -1
        if accelerate_ball:
            mic_speed_x *= speed_multiplier
            mic_speed_y *= speed_multiplier
            # Zrychlení hráče, pokud je režim zrychlování aktivní
            hrac_speed *= speed_multiplier
            cpu_speed *= speed_multiplier

    # Kolize s CPU
    if mic.colliderect(cpu):
        mic_speed_x *= -1
        if accelerate_ball:
            mic_speed_x *= speed_multiplier
            mic_speed_y *= speed_multiplier
            # Zrychlení CPU, pokud je režim zrychlování aktivní
            hrac_speed *= speed_multiplier
            cpu_speed *= speed_multiplier

    # Kolize se středovou platformou
    if mic.colliderect(stredova_platforma):
        mic_speed_x *= -1
        if accelerate_ball:
            mic_speed_x *= speed_multiplier
            mic_speed_y *= speed_multiplier
            # Zrychlení, pokud je režim zrychlování aktivní
            hrac_speed *= speed_multiplier
            cpu_speed *= speed_multiplier

    # Kolize s hráčem 2 (pro režim dvou hráčů)
    if herni_rezim == "hrac" and mic.colliderect(hrac2):
        mic_speed_x *= -1
        if accelerate_ball:
            mic_speed_x *= speed_multiplier
            mic_speed_y *= speed_multiplier
            # Zrychlení hráčů 2, pokud je režim zrychlování aktivní
            hrac_speed *= speed_multiplier

            hrac2_speed *= speed_multiplier  
# Pohyb hráče
def pohyb_hrace():
    if accelerate_ball:
        hrac.y += hrac_speed * speed_multiplier
    else:
        hrac.y += hrac_speed

    if hrac.top <= 0:
        hrac.top = 0
    if hrac.bottom >= vyska_okna:
        hrac.bottom = vyska_okna


# Pohyb hráče 2 (pro režim dvou hráčů)
def pohyb_hrace_2():
    hrac2.y += hrac2_speed
    if hrac2.top <= 0:
        hrac2.top = 0
    if hrac2.bottom >= vyska_okna:
        hrac2.bottom = vyska_okna

# Pohyb středové platformy
def pohyb_stredove_platformy():
    global smer
    rychlost_platformy = 8  # Jak rychle se bude platforma pohybovat

    stredova_platforma.y += smer * rychlost_platformy

    # Když platforma narazí na horní nebo dolní okraj, změní směr
    if stredova_platforma.top <= 0 or stredova_platforma.bottom >= vyska_okna:
        smer *= -1

# Restart míče
def mic_restart():
    global mic_speed_x, mic_speed_y
    mic.center = (sirka_okna / 2, vyska_okna / 2)
    mic_speed_x = 8 * (-1 if mic_speed_x > 0 else 1)
    mic_speed_y = 8 * (-1 if mic_speed_y > 0 else 1)

# Zobrazení hlavního menu
def zobraz_menu():
    screen.fill("black")
    title_surface = menu_font.render("PONG HRA", True, "white")
    option1_surface = menu_font.render("1. Hrát proti CPU", True, "white")
    option2_surface = menu_font.render("2. Hrát proti hráči", True, "white")
    option3_surface = menu_font.render("3. Zobrazit historii zápasů", True, "white")
    option4_surface = menu_font.render(f"4. Režim zrychlování míče: {'Zapnuto' if accelerate_ball else 'Vypnuto'}", True, "white")

    screen.blit(title_surface, (sirka_okna / 2 - title_surface.get_width() / 2, 100))
    screen.blit(option1_surface, (sirka_okna / 2 - option1_surface.get_width() / 2, 200))
    screen.blit(option2_surface, (sirka_okna / 2 - option2_surface.get_width() / 2, 300))
    screen.blit(option3_surface, (sirka_okna / 2 - option3_surface.get_width() / 2, 400))
    screen.blit(option4_surface, (sirka_okna / 2 - option4_surface.get_width() / 2, 500))

    pygame.display.update()

# Zobrazení menu s historií zápasů
def zobraz_historii():
    screen.fill("black")
    history_title = menu_font.render("Historie zápasů", True, "white")
    back_option = menu_font.render("1. Zpět do menu", True, "white")
    clear_option = menu_font.render("2. Vymazat historii", True, "white")

    screen.blit(history_title, (sirka_okna / 2 - history_title.get_width() / 2, 100))
    screen.blit(back_option, (sirka_okna / 2 - back_option.get_width() / 2, 300))
    screen.blit(clear_option, (sirka_okna / 2 - clear_option.get_width() / 2, 400))

    # Načtení historie zápasů
    cursor.execute("SELECT player_score, cpu_score FROM history ORDER BY id DESC LIMIT 5")
    history = cursor.fetchall()
    for i, (player_score, cpu_score) in enumerate(history):
        history_text = f"Hráč: {player_score} - CPU: {cpu_score}"
        history_surface = menu_font.render(history_text, True, "white")
        screen.blit(history_surface, (50, 650 + i * 30))

    pygame.display.update()

# Nastavení okna
sirka_okna = 1280
vyska_okna = 800
screen = pygame.display.set_mode((sirka_okna, vyska_okna))
pygame.display.set_caption("Pong Hra")

# Clock
clock = pygame.time.Clock()

# Vytvoření míče
mic = pygame.Rect(0, 0, 30, 30)
mic.center = (sirka_okna / 2, vyska_okna / 2)

# Vytvoření CPU
cpu = pygame.Rect(0, 0, 20, 100)
cpu.centery = vyska_okna / 2

# Vytvoření hráče
hrac = pygame.Rect(0, 0, 20, 100)
hrac.midright = (sirka_okna, vyska_okna / 2)
hrac_speed = 0

# Vytvoření hráče 2 (pro režim dvou hráčů)
hrac2 = pygame.Rect(0, 0, 20, 100)
hrac2.midleft = (0, vyska_okna / 2)  # Posunutí na správnou pozici
hrac2_speed = 0

# Vytvoření středové platformy
stredova_platforma = pygame.Rect(0, 0, 20, 100)  # Vytvoření platformy ve středu
stredova_platforma.center = (sirka_okna / 2, vyska_okna/1.1)

# Vytvoření středové čáry
line = pygame.Rect(0, 0, 5, vyska_okna)
line.centerx = sirka_okna / 2

# Herní režim
herni_rezim = None

# Hlavní smyčka
while True:
    if herni_rezim is None:
        zobraz_menu()
        # Resetování skóre při návratu do menu
        cpu_points, hrac_points = 0, 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    herni_rezim = "cpu"
                elif event.key == pygame.K_2:
                    herni_rezim = "hrac"
                elif event.key == pygame.K_3:
                    herni_rezim = "historie"
                elif event.key == pygame.K_4:
                    accelerate_ball = not accelerate_ball
    elif herni_rezim == "historie":
        zobraz_historii()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # Zpět do menu
                    herni_rezim = None
                elif event.key == pygame.K_2:  # Vymazání historie
                    cursor.execute("DELETE FROM history")
                    conn.commit()
                    print("Historie zápasů byla vymazána.")
                    herni_rezim = "historie"  # Zůstat v historii

    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if herni_rezim == "cpu":
                    if event.key == pygame.K_UP:
                        hrac_speed = -8
                    if event.key == pygame.K_DOWN:
                        hrac_speed = 8
                elif herni_rezim == "hrac":
                    if event.key == pygame.K_w:
                        hrac2_speed = -8
                    if event.key == pygame.K_s:
                        hrac2_speed = 8
                    if event.key == pygame.K_UP:
                        hrac_speed = -8
                    if event.key == pygame.K_DOWN:
                        hrac_speed = 8
            if event.type == pygame.KEYUP:
                if herni_rezim == "cpu" and event.key in (pygame.K_UP, pygame.K_DOWN):
                    hrac_speed = 0
                elif herni_rezim == "hrac" and event.key in (pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN):
                    if event.key in (pygame.K_w, pygame.K_s):
                        hrac2_speed = 0
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        hrac_speed = 0

        # Pohyb CPU nebo hráče 2
        if herni_rezim == "cpu":
            pohyb_cpu()
        elif herni_rezim == "hrac":
            pohyb_hrace_2()

        # Pohyb středové platformy
        pohyb_stredove_platformy()

        # Pohyb míče
        kolize_mice()

        # Pohyb hráče
        pohyb_hrace()

        # Kreslení herních objektů
        screen.fill("black")
        cpu_score_surface = score_font.render(str(cpu_points), True, "white")
        hrac_score_surface = score_font.render(str(hrac_points), True, "white")
        screen.blit(cpu_score_surface, (sirka_okna / 4, 20))
        screen.blit(hrac_score_surface, (3 * sirka_okna / 4, 20))
        pygame.draw.rect(screen, "blue", line)
        pygame.draw.ellipse(screen, "white", mic)
        if herni_rezim == "cpu":
            pygame.draw.rect(screen, "white", cpu)  # CPU platforma
            pygame.draw.rect(screen, "white", hrac)  # Hráč platforma
        elif herni_rezim == "hrac":
            pygame.draw.rect(screen, "white", hrac2)  # Hráč 2 platforma
            pygame.draw.rect(screen, "white", hrac)  # Hráč 1 platforma

        # Kreslení středové platformy
        pygame.draw.rect(screen, "green", stredova_platforma)

        # Aktualizace obrazovky
        pygame.display.update()
        clock.tick(60)

        # Kontrola konce hry
        if cpu_points >= 5 or hrac_points >= 5:
            cursor.execute("INSERT INTO history (player_score, cpu_score) VALUES (?, ?)", (hrac_points, cpu_points))
            conn.commit()
            herni_rezim = None
            cpu_points, hrac_points = 0, 0
