import pygame
import sys
import threading
import time
from assets import *

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)

screen = pygame.display.set_mode((1280, 720))

# Game variables
FPS = 60
clock = pygame.time.Clock()
Score = 0
waiting_flag = True
game_over_flag = False
projectile_active = False
projectile_top_active = False
midpoint_sound_flag_First_Time = False
projectile_speed = 20
swing_timer = 80

# Events (not really Eventful)
swing_event = threading.Event()
hit_event = threading.Event()

# Positions
projectile_y = 515
projectile_top_y = projectile_y - 150
projectile_width = 50
projectile_height = 50
projectile_position = 0
projectile_top_position = 0

# Locks for threading
lock = threading.Lock()
score_lock = threading.Lock()

# Rectangles
baseball = pygame.Rect(200, 500, 50, 50)
second_baseball = pygame.Rect(200, 350, 50, 50)
launcher = pygame.Rect(1080, 500, 50, 50)
midpoint = (launcher.left + baseball.right) / 2 + 20

# Threads
projectile_thread = None
projectile_top_thread = None
flying_projectiles = []

# Projectile class handles projectile movement and collision detection
class Projectile(threading.Thread):
    def __init__(self, x_position, y_position, width, height, speed):
        threading.Thread.__init__(self)
        self.daemon = True
        self.x_position = x_position
        self.y_position = y_position
        self.width = width
        self.height = height
        self.speed = speed
        self.active = True
        self.midpoint_passed = False
        self.angle = 0

    def run(self):
        global projectile_position, projectile_active, game_over_flag
        midpoint = (launcher.right + baseball.left) / 2
        while self.active:
            with lock:
                self.x_position -= self.speed
                projectile_position = self.x_position       # It went from thread calculating position to this, children really grow up fast
                self.angle = (self.angle + 10) % 360

            if not self.midpoint_passed and self.x_position <= midpoint:
                metronome_sound.play()
                self.midpoint_passed = True

            time.sleep(1 / FPS)

            with lock:
                if self.x_position < baseball.left - 80 and not waiting_flag and not game_over_flag:
                    game_over_flag = True
                    projectile_active = False
                    swing_event.set()

# Similar class for top projectile (basically copy pasta)
class Projectile_Top(threading.Thread):
    def __init__(self, x_position, y_position, width, height, speed):
        threading.Thread.__init__(self)
        self.daemon = True
        self.x_position = x_position
        self.y_position = y_position
        self.width = width
        self.height = height
        self.speed = speed
        self.active = True
        self.midpoint_passed = False
        self.angle = 0

    def run(self):
        global projectile_top_position, projectile_top_active, game_over_flag
        while self.active:
            with lock:
                self.x_position -= self.speed
                projectile_top_position = self.x_position
                self.angle = (self.angle + 10) % 360

            time.sleep(1 / FPS)

            with lock:
                if self.x_position < baseball.left - 80 and not waiting_flag and not game_over_flag:
                    game_over_flag = True
                    projectile_top_active = False
                    swing_event.set()

# Basically Handles the flying projectiles after they are hit for the heck for it
class FlyingProjectile(threading.Thread):
    def __init__(self, x_position, y_position):
        threading.Thread.__init__(self)
        self.daemon = True
        self.x_position = x_position
        self.y_position = y_position
        self.active = True
        self.angle = 0

    def run(self):
        while self.active:
            with lock:
                self.x_position += 25
                self.y_position -= 25
                self.angle = (self.angle + 30) % 360

                if self.x_position > 1280 or self.y_position < 0:
                    self.active = False

            time.sleep(1 / FPS)

# Handles the baseball object (YOU!) and its interactions
class Baseball(threading.Thread):
    def __init__(self, rect, color):
        threading.Thread.__init__(self)
        self.daemon = True
        self.rect = rect
        self.color = color
        self.active = True

    def run(self):
        global Score, waiting_flag, game_over_flag, projectile_position, projectile_top_position
        while self.active:
            time.sleep(1 / FPS)

            with lock:
                # Check collision with projectile
                if self.rect.colliderect(pygame.Rect(projectile_position, projectile_y, projectile_width, projectile_height)):
                    if self.color == red and projectile_active:
                        hit_event.set()
                        flying_projectile = FlyingProjectile(projectile_position, projectile_y)
                        flying_projectile.start()
                        flying_projectiles.append(flying_projectile)
                        reset_and_restart_projectile(is_top=False)
                # Check collision with top projectile
                if self.rect.colliderect(pygame.Rect(projectile_top_position, projectile_top_y, projectile_width, projectile_height)):
                    if self.color == red and projectile_top_active:
                        hit_event.set()
                        flying_projectile = FlyingProjectile(projectile_top_position, projectile_top_y)
                        flying_projectile.start()
                        flying_projectiles.append(flying_projectile)
                        reset_and_restart_projectile(is_top=True)

            with lock:
                if game_over_flag or waiting_flag:
                    self.color = green

    def stop(self):
        self.active = False

# Manages the game score (another one that grew from "add +1 points to a global variable and deactivate" into something)
class ScoreManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        global Score
        while True:
            hit = hit_event.wait(0.5)
            if hit:
                with score_lock:
                    Score += 2
                hit_event.clear()

            swing = swing_event.wait(0.1)
            if swing:
                swing_event.clear()
                with score_lock:
                    if not hit_event.is_set():
                        Score -= 1
                        if Score < 0:      # This is horrible, that's the dumbest solution ever for race condition XD
                            Score = 0

# Plays the metronome sound (duh)
def metronome_play(sound, status):
    if status['active']:
        sound.play()
        status['active'] = False                # My first thread ever, look how far we've came :D

# Functions for use in Projectile thread
# This one starts main projectile
def start_projectile():
    global projectile_thread, projectile_position, projectile_active
    if projectile_thread and projectile_thread.is_alive():
        projectile_thread.active = False

    projectile_position = launcher.left
    projectile_active = True
    projectile_thread = Projectile(launcher.left, projectile_y, projectile_width, projectile_height, projectile_speed)
    projectile_thread.start()

# This one starts the double mode exclusive, the one and only, Top Projectile!!!!!!
def start_projectile_top():
    global projectile_top_thread, projectile_top_position, projectile_top_active
    if projectile_top_thread and projectile_top_thread.is_alive():
        projectile_top_thread.active = False

    projectile_top_position = launcher.left
    projectile_top_active = True
    projectile_top_thread = Projectile_Top(launcher.left, projectile_top_y, projectile_width, projectile_height, projectile_speed)
    projectile_top_thread.start()

# Resets and restarts a projectile after it has been hit    
def reset_and_restart_projectile(is_top=False):
    global projectile_thread, projectile_position, projectile_active
    global projectile_top_thread, projectile_top_position, projectile_top_active

    if is_top:
        if projectile_top_thread and projectile_top_thread.is_alive():      # Turns out merging two really similar functions makes code more readable
            projectile_top_thread.active = False
        projectile_top_position = launcher.left
        projectile_top_active = False
        start_projectile_top()
    else:
        if projectile_thread and projectile_thread.is_alive():
            projectile_thread.active = False
        projectile_position = launcher.left
        projectile_active = False
        start_projectile()

# Main menu (barebones but it's good enough so whatever)
def show_menu():
    menu_active = True
    mode = None
    while menu_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    mode = 'normalny'
                    menu_active = False
                elif event.key == pygame.K_SPACE:
                    mode = 'podwojny'
                    menu_active = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        screen.blit(other_background_image, (0, 0))
        title_text = large_font.render("Gierka bez nazwy - wybierz Trzyb", True, white)
        start_text = font.render("Enter - Normalny", True, white)
        practice_text = font.render("Spacja - Podwójny", True, white)
        quit_text = font.render("Escape - Wyjdź", True, white)

        screen.blit(title_text, title_text.get_rect(center=(640, 200)))
        screen.blit(start_text, start_text.get_rect(center=(640, 350)))
        screen.blit(practice_text, practice_text.get_rect(center=(640, 400)))
        screen.blit(quit_text, quit_text.get_rect(center=(640, 450)))

        pygame.display.flip()
        clock.tick(15)
    return mode

# The Game with a single projectile
def base_game():
    global waiting_flag, game_over_flag, Score, projectile_position, projectile_active
    #   Activating the initial threads
    baseball_thread = Baseball(baseball, green)
    baseball_thread.start()

    score_manager = ScoreManager()
    score_manager.start()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                try:
                    if projectile_thread and projectile_thread.is_alive():
                        projectile_thread.active = False
                        projectile_thread.join()

                    if baseball_thread and baseball_thread.is_alive():
                        baseball_thread.stop()
                        baseball_thread.join()      # Absorbing the threads to properly close the game :)
                except Exception as e:
                    print(f"Error stopping threads: {e}")
                finally:
                    pygame.quit()
                    sys.exit(0)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_z and not game_over_flag:

                # Setting an event, s i stanu machnięcia (oryginalnie był to kolor kwadratu, tak pozostało)
                swing_event.set()
                baseball_thread.color = red     
                pygame.time.set_timer(pygame.USEREVENT, swing_timer)
                if waiting_flag:
                    waiting_flag = False    # Initial start of the gme
                    start_projectile()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_x and game_over_flag:

                # Reseting everything back to initial state after restarting the game
                Score = 0
                waiting_flag = True
                game_over_flag = False
                baseball_thread.color = green
                if projectile_thread and projectile_thread.is_alive():
                    projectile_thread.active = False
                projectile_position = launcher.right
                projectile_active = False

            if event.type == pygame.USEREVENT:
                baseball_thread.color = green
                pygame.time.set_timer(pygame.USEREVENT, 0)      

        if not waiting_flag:
            with lock:
                if not projectile_active and (projectile_thread is None or not projectile_thread.is_alive()):
                    start_projectile()      #   Ball respawns

        screen.blit(background_image, (0, 0))
        screen.blit(glove_image, (1080, 500))

        if baseball_thread.is_alive():
            if baseball_thread.color == red:
                rotated_image = pygame.transform.rotate(baseball_image, -90)
                screen.blit(rotated_image, baseball_thread.rect.topleft)    #   Display of the swing
            else:
                screen.blit(baseball_image, baseball_thread.rect.topleft)

        with lock:

            #   Ball rotation mechanism (it looks cool)
            if projectile_position + projectile_width > 0 and projectile_active:
                rotated_projectile_image = pygame.transform.rotate(projectile_image, projectile_thread.angle)
                new_ball_offset = rotated_projectile_image.get_rect(center=(projectile_position + projectile_width // 2, projectile_y + projectile_height // 2))
                screen.blit(rotated_projectile_image, new_ball_offset)      

            #  Ball rotation for the balls that fly away
            for i in flying_projectiles:
                if i.active:
                    rotated_projectile_image = pygame.transform.rotate(projectile_image, i.angle)
                    new_ball_offset = rotated_projectile_image.get_rect(center=(i.x_position + projectile_width // 2, i.y_position + projectile_height // 2))
                    screen.blit(rotated_projectile_image, new_ball_offset.topleft)
                else:
                    flying_projectiles.remove(i)

        score_text = font.render(f'Score: {Score}', True, white)    #If professor is reading it for some reason, I hope you know you're really cool (⌐■_■)
        screen.blit(score_text, (10, 10))

        if game_over_flag:
            screen.blit(other_background_image, (0, 0))
            game_over_text = font.render('Porazka, wcisnij X aby zresetowac!', True, white)
            screen.blit(game_over_text, (320, 340))

        pygame.display.flip()

# Double the projectile, double the trouble (This should've been written better with less copy pasta, but 3rd term was on a time crunch)
def double_game():

    # Not gonna make comments for this mode, it's really similar to single
    global waiting_flag, game_over_flag, Score, projectile_position, projectile_active, projectile_top_position, projectile_top_active, midpoint_sound_flag_First_Time
    baseball_thread = Baseball(baseball, green)
    baseball_thread.start()

    second_baseball_thread = Baseball(second_baseball, green)
    second_baseball_thread.start()

    score_manager = ScoreManager()
    score_manager.start()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                try:
                    if projectile_thread and projectile_thread.is_alive():
                        projectile_thread.active = False
                        projectile_thread.join()

                    if baseball_thread and baseball_thread.is_alive():
                        baseball_thread.stop()
                        baseball_thread.join()

                    if projectile_top_thread and projectile_top_thread.is_alive():
                        projectile_top_thread.active = False
                        projectile_top_thread.join()

                    if second_baseball_thread and second_baseball_thread.is_alive():
                        second_baseball_thread.stop()
                        second_baseball_thread.join()
                except Exception as e:
                    print(f"Error stopping threads: {e}")
                finally:
                    pygame.quit()
                    sys.exit(0)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_z and not game_over_flag:
                swing_event.set()
                baseball_thread.color = red
                pygame.time.set_timer(pygame.USEREVENT, swing_timer)
                if waiting_flag:
                    waiting_flag = False
                    start_projectile()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_x and not game_over_flag:
                swing_event.set()
                second_baseball_thread.color = red
                pygame.time.set_timer(pygame.USEREVENT, swing_timer)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_c and game_over_flag:
                Score = 0
                waiting_flag = True
                game_over_flag = False
                baseball_thread.color = green
                second_baseball_thread.color = green
                if projectile_thread and projectile_thread.is_alive():
                    projectile_thread.active = False
                if projectile_top_thread and projectile_top_thread.is_alive():
                    projectile_top_thread.active = False
                projectile_position = launcher.right
                projectile_active = False
                projectile_top_active = False
                projectile_top_position = launcher.right
                midpoint_sound_flag_First_Time = False

            if event.type == pygame.USEREVENT:
                baseball_thread.color = green
                second_baseball_thread.color = green
                pygame.time.set_timer(pygame.USEREVENT, 0)

        if not waiting_flag:
            with lock:
                if not projectile_active and (projectile_thread is None or not projectile_thread.is_alive()):
                    start_projectile()

        if not midpoint_sound_flag_First_Time and projectile_thread and projectile_thread.is_alive() and projectile_thread.x_position <= midpoint:
            with lock:
                if not projectile_top_active and (projectile_top_thread is None or not projectile_top_thread.is_alive()):
                    start_projectile_top()
                    midpoint_sound_flag_First_Time = True

        screen.blit(background_image, (0, 0))
        screen.blit(glove_image, (1080, 500))
        screen.blit(glove_image, (1080, 350))

        if baseball_thread.is_alive():
            if baseball_thread.color == red:
                rotated_image = pygame.transform.rotate(baseball_image, -90)
                screen.blit(rotated_image, baseball_thread.rect.topleft)
            else:
                screen.blit(baseball_image, baseball_thread.rect.topleft)

        if second_baseball_thread.is_alive():
            if second_baseball_thread.color == red:
                rotated_image = pygame.transform.rotate(baseball_image, -90)
                screen.blit(rotated_image, second_baseball_thread.rect.topleft)
            else:
                screen.blit(baseball_image, second_baseball_thread.rect.topleft)

        with lock:
            if projectile_position + projectile_width > 0 and projectile_active:
                rotated_projectile_image = pygame.transform.rotate(projectile_image, projectile_thread.angle)
                new_ball_offset = rotated_projectile_image.get_rect(center=(projectile_position + projectile_width // 2, projectile_y + projectile_height // 2))
                screen.blit(rotated_projectile_image, new_ball_offset)

            if projectile_top_position + projectile_width > 0 and projectile_top_active:
                rotated_projectile_image = pygame.transform.rotate(projectile_image, projectile_top_thread.angle)
                new_ball_offset = rotated_projectile_image.get_rect(center=(projectile_top_position + projectile_width // 2, projectile_top_y + projectile_height // 2))
                screen.blit(rotated_projectile_image, new_ball_offset)

            for i in flying_projectiles:
                if i.active:
                    rotated_projectile_image = pygame.transform.rotate(projectile_image, i.angle)
                    new_ball_offset = rotated_projectile_image.get_rect(center=(i.x_position + projectile_width // 2, i.y_position + projectile_height // 2))
                    screen.blit(rotated_projectile_image, new_ball_offset.topleft)
                else:
                    flying_projectiles.remove(i)

        score_text = font.render(f'Score: {Score}', True, white)
        screen.blit(score_text, (10, 10))

        if game_over_flag:
            screen.blit(other_background_image, (0, 0))
            game_over_text = font.render('Porazka, wcisnij C aby zresetowac!', True, white)
            screen.blit(game_over_text, (320, 340))

        pygame.display.flip()


mode = show_menu()
if mode == 'normalny':
    base_game()
elif mode == 'podwojny':
    double_game()
else:
    print("No mode selected or mode not recognized.")