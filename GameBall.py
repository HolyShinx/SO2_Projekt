import pygame
import sys
import threading
import time

def update_projectile(projectile, speed, status):
    while status['active']:
        projectile['x_position'] -= speed   # Wątek obługujący ruch piłeczki
        time.sleep(1/FPS)

def metronome_play(sound, status):
    while status['active']:
        sound.play()
        status['active'] = False  # Wątek który puszcza dzwięk metronomu i się wyłącza

def start_thread(fun, args, status):
    if status.get('thread') and status['thread'].is_alive():
        status['active'] = False
        status['thread'].join()
    status['active'] = True
    status['thread'] = threading.Thread(target=fun, args=args)  # Ogólnikowa funkcja, uruchamia wątek, albo jak jest już                                                            # Już uruchomiony to robi reset
    status['thread'].start()                                    # uruchomiony to go resetuje (dla wygody)


pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)
metronome_sound = pygame.mixer.Sound('metronome.mp3')
midpoint_sound_flag = False
baseball_contact_sound_flag = False


FPS = 60
metronome_interval = 1000
last_metronome_sound = 0

black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
white = (255, 255, 255)
purple = (139, 0, 139)

baseball_color = green
launcher_color = purple

Score = 0

swing_timer = 80
swing_moment = 0
projectile_activate = False
game_over_flag = False

projectile_speed = 10

baseball = pygame.Rect(200, 500, 50, 50)
launcher = pygame.Rect(1080, 500, 50, 50)

midpoint = (launcher.left + baseball.right)/2  # Z jakiegoś powodu .x to koordynaty lewo stronne XD

projectile_dictionary = {'x_position': float(launcher.x)}   # Zapis pozycji w słowniku
projectile = pygame.Rect(int(projectile_dictionary['x_position']), 515, 20, 20)

screen = pygame.display.set_mode((1280, 720))

clock = pygame.time.Clock()

font = pygame.font.Font(None, 36)

projectile_status = {'active': False, 'thread': None}
metronome_status = {'active': False, 'thread': None}

while True:
    clock.tick(FPS)
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            projectile_status['active'] = False
            metronome_status['active'] = False
            sys.exit(0)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_z and game_over_flag == False:
            start_thread(update_projectile, (projectile_dictionary, projectile_speed, projectile_status), projectile_status)
            baseball_color = red
            swing_moment = pygame.time.get_ticks()
            projectile_activate = True
            if projectile.right >= baseball.left and projectile.left <= baseball.right:
                Score += 1
                projectile_dictionary['x_position'] = launcher.x
            else:
                if Score != 0:
                    Score -= 1  # Kara za spamienie przyciskiem xd

        if event.type == pygame.KEYDOWN and event.key == pygame.K_x and game_over_flag == True:
            Score = 0
            game_over_flag = False
            baseball_color = green  # Resetowanie wszystkiego do ustawien domyslych yay
            projectile_dictionary['x_position'] = launcher.x
            if projectile_status['thread']:
                projectile_status['active'] = False
                projectile_status['thread'].join()  # Wątki też
            if metronome_status['thread']:
                metronome_status['active'] = False
                metronome_status['thread'].join()

    if game_over_flag == False:
        if current_time - swing_moment >= swing_timer:
            baseball_color = green

        if projectile_activate:
            projectile.x = int(projectile_dictionary['x_position'])  # Update from shared dictionary
            if projectile.left <= midpoint <= projectile.right and midpoint_sound_flag == False:
                start_thread(metronome_play, (metronome_sound, metronome_status), metronome_status)
                midpoint_sound_flag = True  # flaga przeciwko wielokrotnym odtworzeniu dźwieku na midpoincie

            if baseball.left <= projectile.left <= baseball.right and baseball_contact_sound_flag == False:
                start_thread(metronome_play, (metronome_sound, metronome_status), metronome_status)
                baseball_contact_sound_flag = True

        if projectile.left > midpoint:
            midpoint_sound_flag = False
        if projectile.left > midpoint:
            baseball_contact_sound_flag = False


        if projectile.right < baseball.x:
            game_over_flag = True

        screen.fill(black)
        pygame.draw.rect(screen, baseball_color, baseball)
        pygame.draw.rect(screen, launcher_color, launcher)
        pygame.draw.rect(screen, white, projectile)

        score_text = font.render(f'Score: {Score}', True, white)
        screen.blit(score_text, (10, 10))

    else:
        screen.fill(black)
        game_over_text = font.render('Skill issue, wcisnij X aby zresetowac!', True, white)
        screen.blit(game_over_text, (320, 340))
    pygame.display.flip()