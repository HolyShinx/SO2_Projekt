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

def start_projectile(): 
    global projectile_thread, projectile_position, projectile_active
    if projectile_thread and projectile_thread.is_alive():
        projectile_thread.active = False

    projectile_position = launcher.right
    projectile_active = True
    projectile_thread = Projectile(launcher.right, projectile_y, projectile_width, projectile_height, projectile_speed)
    projectile_thread.start()

def reset_and_restart_projectile():
    global projectile_thread, projectile_position, projectile_active
    if projectile_thread and projectile_thread.is_alive():
        projectile_thread.active = False

    projectile_position = launcher.right
    projectile_active = False

    start_projectile()

projectile_thread = None
lock = threading.Lock()

class Projectile(threading.Thread):
    def __init__(self, x_position, y_position, width, height, speed):
        threading.Thread.__init__(self)
        self.x_position = x_position
        self.y_position = y_position
        self.width = width
        self.height = height
        self.speed = speed
        self.active = True

    def run(self):
        global projectile_position, projectile_active, game_state
        while self.active:
            # Move the projectile
            with lock:
                self.x_position -= self.speed
                projectile_position = self.x_position

            time.sleep(1 / FPS)
            
            # Check if the projectile has missed the baseball and update game staten
            with lock:
                
                global game_over_flag   
                if self.x_position < baseball.left and waiting_flag == False and game_over_flag == False and baseball_color != red:
                    waiting_flag == True
                    game_over_flag = True
                    projectile_active = False


pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)
metronome_sound = pygame.mixer.Sound('metronome.mp3')
midpoint_sound_flag = False
baseball_contact_sound_flag = False


FPS = 60
metronome_interval = 1000
last_metronome_sound = 0
waiting_flag = True
game_over_flag = False

black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
white = (255, 255, 255)
purple = (139, 0, 139)

baseball_color = green
launcher_color = purple

Score = 0

swing_timer = 800
swing_moment = False
projectile_activate = False
projectile_y = 515  # y_position for the projectile
projectile_width = 20
projectile_height = 20
projectile_active = False

projectile_speed = 5

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
shared_game_data = {'projectile_position': launcher.right, 'projectile_active': False}

projectile_position = launcher.right

while True:
    clock.tick(FPS)
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if projectile_thread and projectile_thread.is_alive():
                projectile_thread.active = False
                projectile_thread.join()
            sys.exit(0)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_z and game_over_flag == False:
            if waiting_flag == True:
                waiting_flag = False
                start_projectile()

            swing_moment = True
            baseball_color = red
            pygame.time.set_timer(pygame.USEREVENT, swing_timer)


            #else:
                #if Score != 0:
                    #Score -= 1      #Kara za spam przyciskiem xd


        if event.type == pygame.KEYDOWN and event.key == pygame.K_x and game_over_flag == True:
            Score = 0
            waiting_flag = True
            game_over_flag = False
            baseball_color = green
            if projectile_thread and projectile_thread.is_alive():
                projectile_thread.active = False
            projectile_position = launcher.right
            projectile_active = False

        if event.type == pygame.USEREVENT:
            baseball_color = green
            pygame.time.set_timer(pygame.USEREVENT, 0)
            swing_moment = False



    if waiting_flag == False:
        with lock:
            if not projectile_active and (projectile_thread is None or not projectile_thread.is_alive()):
                start_projectile()

            # Check collision
            if baseball.colliderect(pygame.Rect(projectile_position, projectile_y, projectile_width, projectile_height)):
                if baseball_color == red and projectile_active:
                    Score += 1
                    metronome_sound.play()
                    reset_and_restart_projectile()

    screen.fill(black)
    pygame.draw.rect(screen, baseball_color, baseball)
    pygame.draw.rect(screen, launcher_color, launcher)

    with lock:
        if projectile_position + projectile_width > 0 and projectile_active:
            pygame.draw.rect(screen, white, (projectile_position, projectile_y, projectile_width, projectile_height))
        elif not projectile_active:
            # Reset projectile visually and positionally when hit
            projectile_position = launcher.right

    score_text = font.render(f'Score: {Score}', True, white)
    screen.blit(score_text, (10, 10))

    if game_over_flag == True:
        screen.fill(black)
        game_over_text = font.render('Skill issue, wcisnij X aby zresetowac!', True, white)
        screen.blit(game_over_text, (320, 340))
    pygame.display.flip()
