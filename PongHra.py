# Pong hra s power-upy a rozšířenými herními mechanismy

# Import potřebných knihoven pro herní vývoj a funkcionalitu
import pygame    # Knihovna pro tvorbu her a multimedální aplikace
import sys       # Systémové operace a ukončení programu
import sqlite3   # Práce s databází pro ukládání herní historie
import random    # Generování náhodných hodnot
import time      # Práce s časem a měřením intervalů

# Inicializace proměnné pro směr pohybu střední platformy
smer = 1

# Inicializace Pygame knihovny
pygame.init()

# Nastavení základních herních parametrů
mic_speed_x = 8             # Horizontální rychlost míče
mic_speed_y = 8             # Vertikální rychlost míče
cpu_speed = 8               # Rychlost CPU hráče
speed_multiplier = 1.1       # Faktor zrychlení míče
accelerate_ball = False      # Příznak aktivace zrychlování míče
cpu_points, hrac_points = 0, 0  # Počítadlo bodů pro CPU a hráče

# Nastavení fontů pro různé textové prvky
score_font = pygame.font.Font(None, 100)  # Font pro zobrazení skóre
menu_font = pygame.font.Font(None, 60)    # Font pro menu

# Připojení k SQLite databázi pro ukládání herní historie
conn = sqlite3.connect("game_history.db")
cursor = conn.cursor()

# Vytvoření tabulky pro historii zápasů, pokud ještě neexistujes
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_score INTEGER,
    cpu_score INTEGER
)
""")
conn.commit()

# Třída pro definici power-upů s vlastnostmi a chováním
class PowerUp:
    def __init__(self, x, y, typ, barva, velikost=20):
        self.rect = pygame.Rect(x, y, velikost, velikost)  # Obdélník power-upu
        self.typ = typ          # Typ power-upu
        self.barva = barva      # Barva power-upu
        self.aktivni = True     # Zda je power-up aktivní
        self.efekt_cas = 3      # Doba trvání efektu v sekundách

# Seznamy pro správu aktivních power-upů a jejich efektů
aktivni_powerupy = []     # Aktuálně viditelné power-upy
aktivni_efekty = []       # Aktivní efekty power-upů

# Definice typů power-upů a jejich barev
powerup_typy = {
    "zrychleni_mice": "red",       # Zrychlení míče
    "zpomaleni_mice": "blue",      # Zpomalení míče
    "zvetseni_palky": "green",     # Zvětšení pálky hráče
    "zmenseni_palky_cpu": "purple",# Zmenšení pálky CPU
    "dvojity_bod": "yellow",       # Příští bod se počítá dvakrát
    "neviditelny_mic": "white",    # Míč se stane neviditelným
}

# Původní velikosti a rychlosti pro reset efektů
puvodni_velikost_hrace = 100
puvodni_velikost_cpu = 100
puvodni_rychlost_x = 8
puvodni_rychlost_y = 8

# Funkce pro vytvoření nového power-upu s náhodnou pozicí
def vytvor_powerup():
    # Náhodný výběr typu a barvy power-upu
    typ = random.choice(list(powerup_typy.keys()))
    barva = powerup_typy[typ]
   
    # Náhodné umístění power-upu v herním prostoru
    x = random.randint(100, sirka_okna - 100)
    y = random.randint(100, vyska_okna - 100)
   
    # Vytvoření power-upu a zajištění, aby nebyl v kolizi s herními objekty
    powerup = PowerUp(x, y, typ, barva)
   
    while (powerup.rect.colliderect(mic) or
           powerup.rect.colliderect(hrac) or
           powerup.rect.colliderect(cpu) or
           powerup.rect.colliderect(stredova_platforma)):
        x = random.randint(100, sirka_okna - 100)
        y = random.randint(100, vyska_okna - 100)
        powerup.rect = pygame.Rect(x, y, 20, 20)
   
    aktivni_powerupy.append(powerup)

# Funkce pro aktivaci power-upů s různými herními efekty
def aktivuj_powerup(powerup):
    global mic_speed_x, mic_speed_y, hrac, cpu
   
    # Výpočet času expirace efektu
    expiraci_cas = time.time() + powerup.efekt_cas
   
    # Specifické efekty pro různé typy power-upů
    if powerup.typ == "zrychleni_mice":
        mic_speed_x *= 1.5
        mic_speed_y *= 1.5
        aktivni_efekty.append({"typ": "zrychleni_mice", "expiraci_cas": expiraci_cas})
   
    elif powerup.typ == "zpomaleni_mice":
        mic_speed_x /= 1.5
        mic_speed_y /= 1.5
        aktivni_efekty.append({"typ": "zpomaleni_mice", "expiraci_cas": expiraci_cas})
   
    elif powerup.typ == "zvetseni_palky":
        # Zvětšení pálky hráče s omezením maximální velikosti
        nova_vyska = min(200, hrac.height * 1.5)
        rozdil = nova_vyska - hrac.height
        hrac.height = nova_vyska
        hrac.y -= rozdil / 2
        aktivni_efekty.append({"typ": "zvetseni_palky", "expiraci_cas": expiraci_cas})
   
    elif powerup.typ == "zmenseni_palky_cpu":
        # Zmenšení pálky CPU s omezením minimální velikosti
        nova_vyska = max(30, cpu.height / 1.5)
        rozdil = cpu.height - nova_vyska
        cpu.height = nova_vyska
        cpu.y += rozdil / 2
        aktivni_efekty.append({"typ": "zmenseni_palky_cpu", "expiraci_cas": expiraci_cas})
   
    elif powerup.typ == "dvojity_bod":
        # Přidání efektu dvojitého bodu
        aktivni_efekty.append({"typ": "dvojity_bod", "expiraci_cas": expiraci_cas})
   
    elif powerup.typ == "neviditelny_mic":
        # Přidání efektu neviditelného míče
        aktivni_efekty.append({"typ": "neviditelny_mic", "expiraci_cas": expiraci_cas})

# Funkce pro kontrolu a vypršení aktivních efektů
def kontroluj_efekty():
    global mic_speed_x, mic_speed_y, hrac, cpu, aktivni_efekty
   
    aktualni_cas = time.time()
    nove_efekty = []
   
    # Procházení aktivních efektů a jejich reset po vypršení
    for efekt in aktivni_efekty:
        if aktualni_cas >= efekt["expiraci_cas"]:
            # Reset rychlosti míče
            if efekt["typ"] == "zrychleni_mice" or efekt["typ"] == "zpomaleni_mice":
                mic_speed_x = puvodni_rychlost_x * (1 if mic_speed_x > 0 else -1)
                mic_speed_y = puvodni_rychlost_y * (1 if mic_speed_y > 0 else -1)
           
            # Reset velikosti pálky hráče
            elif efekt["typ"] == "zvetseni_palky":
                rozdil = hrac.height - puvodni_velikost_hrace
                hrac.height = puvodni_velikost_hrace
                hrac.y += rozdil / 2
           
            # Reset velikosti pálky CPU
            elif efekt["typ"] == "zmenseni_palky_cpu":
                rozdil = puvodni_velikost_cpu - cpu.height
                cpu.height = puvodni_velikost_cpu
                cpu.y -= rozdil / 2
        else:
            nove_efekty.append(efekt)
   
    aktivni_efekty = nove_efekty

# Funkce pro pohyb CPU hráče s implementací umělé inteligence
def pohyb_cpu():
    # Pravděpodobnost chyby CPU pro nepřesný pohyb
    pravdepodobnost_chyby = 0.08
    if random.random() < pravdepodobnost_chyby:
        return  # Někdy CPU neprovede žádný pohyb

    max_cpu_speed = 8  # Omezení maximální rychlosti CPU
    rozdil = mic.centery - cpu.centery

    # Pohyb CPU podle pozice míče s mírným zpožděním
    if rozdil > 10:  
        cpu.y += min(max_cpu_speed, abs(rozdil))
    elif rozdil < -10:
        cpu.y -= min(max_cpu_speed, abs(rozdil))

    # Omezení pohybu CPU v herním prostoru
    if cpu.top <= 0:
        cpu.top = 0
    if cpu.bottom >= vyska_okna:
        cpu.bottom = vyska_okna

# Funkce pro řešení kolizí míče s herními objekty
def kolize_mice():
    global mic_speed_x, mic_speed_y, cpu_points, hrac_points, hrac_speed, cpu_speed, hrac2_speed

    # Pohyb míče podle aktuální rychlosti
    mic.x += mic_speed_x
    mic.y += mic_speed_y

    # Odraz od horního a dolního okraje obrazovky
    if mic.top <= 0 or mic.bottom >= vyska_okna:
        mic_speed_y *= -1

    # Bod pro CPU, když míč opustí pravou stranu
    if mic.right >= sirka_okna:
        pridat_body("cpu")
        mic_restart()
        stredova_platforma.center = (sirka_okna / 2, vyska_okna/1.1)

    # Bod pro hráče, když míč opustí levou stranu
    if mic.left <= 0:
        pridat_body("hrac")
        mic_restart()
        stredova_platforma.center = (sirka_okna / 2, vyska_okna/1.1)
       
    # Kontrola kolize s power-upy
    for powerup in list(aktivni_powerupy):
        if mic.colliderect(powerup.rect) and powerup.aktivni:
            aktivuj_powerup(powerup)
            aktivni_powerupy.remove(powerup)
    
    # Odrazy míče v módu CPU
    if herni_rezim == "cpu":
        if mic.colliderect(hrac) or mic.colliderect(cpu):
            mic_speed_x *= -1
            
            # Přidání náhodného úhlu při odrazu
            random_angle = random.uniform(-0.5, 0.5)
            mic_speed_y += random_angle * abs(mic_speed_x)
            
            if accelerate_ball:
                mic_speed_x *= speed_multiplier
                mic_speed_y *= speed_multiplier
                hrac_speed *= speed_multiplier
                cpu_speed *= speed_multiplier
    
    # Odrazy míče v módu multiplayer
    if herni_rezim == "hrac":
        if mic.colliderect(hrac):  # Odraz od pravého hráče
            mic_speed_x *= -1
            
            random_angle = random.uniform(-0.5, 0.5)
            mic_speed_y += random_angle * abs(mic_speed_x)
            
            if accelerate_ball:
                mic_speed_x *= speed_multiplier
                mic_speed_y *= speed_multiplier
                hrac_speed *= speed_multiplier
        
        if mic.colliderect(hrac2):  # Odraz od levého hráče
            mic_speed_x *= -1
            
            random_angle = random.uniform(-0.5, 0.5)
            mic_speed_y += random_angle * abs(mic_speed_x)
            
            if accelerate_ball:
                mic_speed_x *= speed_multiplier
                mic_speed_y *= speed_multiplier
                hrac2_speed *= speed_multiplier

    # Odraz od střední platformy
    if mic.colliderect(stredova_platforma):
        mic_speed_x *= -1
        if accelerate_ball:
            mic_speed_x *= speed_multiplier
            mic_speed_y *= speed_multiplier
            hrac_speed *= speed_multiplier
            cpu_speed *= speed_multiplier

# Funkce pro přidání bodů s možností dvojitého bodu
def pridat_body(hrac_typ):
    global cpu_points, hrac_points
   
    body = 1
    # Kontrola aktivního efektu dvojitého bodu
    for efekt in aktivni_efekty:
        if efekt["typ"] == "dvojity_bod":
            body = 2
            aktivni_efekty.remove(efekt)
            break
   
    # Přidání bodů podle typu hráče
    if hrac_typ == "cpu":
        cpu_points += body
    else:
        hrac_points += body

# Funkce pro pohyb hlavního hráče
def pohyb_hrace():
    # Pohyb s možností zrychlení

    hrac.y += hrac_speed

    # Omezení pohybu v herním prostoru
    if hrac.top <= 0:
        hrac.top = 0
    if hrac.bottom >= vyska_okna:
        hrac.bottom = vyska_okna

# Funkce pro pohyb druhého hráče v multiplayer módu
def pohyb_hrace_2():
    hrac2.y += hrac2_speed
   
    # Omezení pohybu v herním prostoru
    if hrac2.top <= 0:
        hrac2.top = 0
    if hrac2.bottom >= vyska_okna:
        hrac2.bottom = vyska_okna

# Funkce pro pohyb střední platformy
def pohyb_stredove_platformy():
    global smer
    rychlost_platformy = 8

    # Pohyb platformy nahoru/dolů s opačným směrem při nárazu do okrajů
    stredova_platforma.y += smer * rychlost_platformy

    if stredova_platforma.top <= 0 or stredova_platforma.bottom >= vyska_okna:
        smer *= -1

# Restart míče po vstřelení gólu
def mic_restart():
    global mic_speed_x, mic_speed_y, aktivni_powerupy, aktivni_efekty
   
    # Reset aktivních efektů a velikostí objektů
    aktivni_efekty = []
   
    hrac.height = puvodni_velikost_hrace
    cpu.height = puvodni_velikost_cpu
   
    # Umístění míče do středu a změna směru
    mic.center = (sirka_okna / 2, vyska_okna / 2)
    mic_speed_x = 8 * (-1 if mic_speed_x > 0 else 1)
    mic_speed_y = 8 * (-1 if mic_speed_y > 0 else 1)
    
    # Reset pozic hráčů do středu své strany
    if herni_rezim == "cpu":
        # Pro CPU mód
        hrac.centery = vyska_okna / 2
        cpu.centery = vyska_okna / 2
    elif herni_rezim == "hrac":
        # Pro multiplayer mód
        hrac.centery = vyska_okna / 2
        hrac2.centery = vyska_okna / 2

# Zobrazení hlavního menu hry
def zobraz_menu():
    screen.fill("black")
   
    # Rendering textových prvků menu
    title_surface = menu_font.render("PONG HRA", True, "white")
    option1_surface = menu_font.render("1. Hrát proti CPU", True, "white")
    option2_surface = menu_font.render("2. Hrát proti hráči", True, "white")
    option3_surface = menu_font.render("3. Zobrazit historii zápasů", True, "white")
    option4_surface = menu_font.render(f"4. Režim zrychlování míče: {'Zapnuto' if accelerate_ball else 'Vypnuto'}", True, "white")

    # Umístění textů na obrazovku
    screen.blit(title_surface, (sirka_okna / 2 - title_surface.get_width() / 2, 100))
    screen.blit(option1_surface, (sirka_okna / 2 - option1_surface.get_width() / 2, 200))
    screen.blit(option2_surface, (sirka_okna / 2 - option2_surface.get_width() / 2, 300))
    screen.blit(option3_surface, (sirka_okna / 2 - option3_surface.get_width() / 2, 400))
    screen.blit(option4_surface, (sirka_okna / 2 - option4_surface.get_width() / 2, 500))

    pygame.display.update()

# Zobrazení menu herní historie
def zobraz_historii():
    screen.fill("black")
   
    # Rendering textů pro historii
# Rendering textů pro historii
    history_title = menu_font.render("Historie zápasů", True, "white")
    back_option = menu_font.render("1. Zpět do menu", True, "white")
    clear_option = menu_font.render("2. Vymazat historii", True, "white")

    screen.blit(history_title, (sirka_okna / 2 - history_title.get_width() / 2, 50))  
    screen.blit(back_option, (sirka_okna / 2 - back_option.get_width() / 2, 350))  
    screen.blit(clear_option, (sirka_okna / 2 - clear_option.get_width() / 2, 450))  


    # Načtení a zobrazení posledních 5 záznamů z databáze
    cursor.execute("SELECT player_score, cpu_score FROM history ORDER BY id DESC LIMIT 5")
    history = cursor.fetchall()
    for i, (player_score, cpu_score) in enumerate(history):
        history_text = f"Hráč: {player_score} - CPU: {cpu_score}"
        history_surface = menu_font.render(history_text, True, "white")
        screen.blit(history_surface, (50, 100 + i * 50))

    pygame.display.update()

# Zobrazení aktivních herních efektů
def zobraz_aktivni_efekty():
    y = 50
    male_font = pygame.font.Font(None, 30)
    for efekt in aktivni_efekty:
        zbyva = round(efekt["expiraci_cas"] - time.time(), 1)
        if zbyva > 0:
            efekt_text = f"{efekt['typ']}: {zbyva} s"
            efekt_surface = male_font.render(efekt_text, True, "white")
            screen.blit(efekt_surface, (10, y))
            y += 30

# Nastavení parametrů herního okna
sirka_okna = 1280
vyska_okna = 800
screen = pygame.display.set_mode((sirka_okna, vyska_okna))
pygame.display.set_caption("Pong Hra s Power-Upy")

# Vytvoření herních objektů
clock = pygame.time.Clock()
mic = pygame.Rect(0, 0, 30, 30)
mic.center = (sirka_okna / 2, vyska_okna / 2)

cpu = pygame.Rect(0, 0, 10, 100)
cpu.centery = vyska_okna / 2

hrac = pygame.Rect(0, 0, 10, 100)
hrac.midright = (sirka_okna, vyska_okna / 2)
hrac_speed = 0

# Objekty pro multiplayer mód
hrac2 = pygame.Rect(0, 0, 10, 100)
hrac2.midleft = (0, vyska_okna / 2)
hrac2_speed = 0

# Střední pohyblivá platforma
stredova_platforma = pygame.Rect(0, 0, 10, 100)
stredova_platforma.center = (sirka_okna / 2, vyska_okna/1.1)

# Střední dělící čára
line = pygame.Rect(0, 0, 1, vyska_okna)
line.centerx = sirka_okna / 2

# Proměnné pro herní logiku
herni_rezim = None
posledni_powerup_cas = 0
powerup_interval = 20  # Interval pro generování power-upů

# Hlavní herní smyčka
while True:
    # Zpracování menu stavů
    if herni_rezim is None:
        zobraz_menu()
       
        # Reset herních proměnných
        cpu_points, hrac_points = 0, 0
        aktivni_powerupy = []
        aktivni_efekty = []
       
        # Zpracování herních událostí
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Volba herního módu
                if event.key == pygame.K_1:
                    herni_rezim = "cpu"
                elif event.key == pygame.K_2:
                    herni_rezim = "hrac"
                elif event.key == pygame.K_3:
                    herni_rezim = "historie"
                elif event.key == pygame.K_4:
                    accelerate_ball = not accelerate_ball

    # Zobrazení herní historie
    elif herni_rezim == "historie":
        zobraz_historii()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    herni_rezim = None
                elif event.key == pygame.K_2:
                    # Vymazání databáze historie
                    cursor.execute("DELETE FROM history")
                    conn.commit()
                    print("Historie zápasů byla vymazána.")
                    herni_rezim = "historie"

    # Hlavní herní smyčka
    else:
        # Zpracování herních událostí a vstupů
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Ovládání hráčů podle herního módu
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
                # Zastavení pohybu hráčů
                if herni_rezim == "cpu" and event.key in (pygame.K_UP, pygame.K_DOWN):
                    hrac_speed = 0
                elif herni_rezim == "hrac" and event.key in (pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN):
                    if event.key in (pygame.K_w, pygame.K_s):
                        hrac2_speed = 0
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        hrac_speed = 0

        # Generování power-upů
        aktualni_cas = time.time()
        if aktualni_cas - posledni_powerup_cas > powerup_interval and len(aktivni_powerupy) < 3:
            vytvor_powerup()
            posledni_powerup_cas = aktualni_cas

        # Aktualizace herních mechanismů
        kontroluj_efekty()

        # Pohyb herních objektů podle herního módu
        if herni_rezim == "cpu":
            pohyb_cpu()
        elif herni_rezim == "hrac":
            pohyb_hrace_2()

        pohyb_stredove_platformy()
        kolize_mice()
        pohyb_hrace()

        # Vykreslení herního prostředí
        screen.fill("black")
        cpu_score_surface = score_font.render(str(cpu_points), True, "white")
        hrac_score_surface = score_font.render(str(hrac_points), True, "white")
        screen.blit(cpu_score_surface, (sirka_okna / 4, 20))
        screen.blit(hrac_score_surface, (3 * sirka_okna / 4, 20))
        pygame.draw.rect(screen, "blue", line)
       
        # Vykreslení míče s efektem neviditelnosti
        neviditelny = any(efekt["typ"] == "neviditelny_mic" for efekt in aktivni_efekty)
       
        if not neviditelny:
            pygame.draw.ellipse(screen, "white", mic)
       
        # Vykreslení hráčů podle herního módu
        if herni_rezim == "cpu":
            pygame.draw.rect(screen, "white", cpu)
            pygame.draw.rect(screen, "white", hrac)
        elif herni_rezim == "hrac":
            pygame.draw.rect(screen, "white", hrac2)
            pygame.draw.rect(screen, "white", hrac)

        pygame.draw.rect(screen, "green", stredova_platforma)
       
        # Vykreslení power-upů
        for powerup in aktivni_powerupy:
            pygame.draw.ellipse(screen, powerup.barva, powerup.rect)
       
        # Zobrazení aktivních efektů
        zobraz_aktivni_efekty()

        # Aktualizace obrazovky
        pygame.display.update()
        clock.tick(60)

        # Kontrola konce hry a uložení výsledku
        if cpu_points >= 5 or hrac_points >= 5:
            cursor.execute("INSERT INTO history (player_score, cpu_score) VALUES (?, ?)", (hrac_points, cpu_points))
            conn.commit()
            herni_rezim = None
            cpu_points, hrac_points = 0, 0