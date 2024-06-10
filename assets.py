import pygame

# Initialize Pygame
pygame.init()

screen = pygame.display.set_mode((1280, 720))

# Load sounds and images
metronome_sound = pygame.mixer.Sound('metronome.mp3')

baseball_image = pygame.image.load('bat.png').convert_alpha()       # I was supposed to separate code into even more files, but it's spaghetti and I'm drowning in it
baseball_image = pygame.transform.scale(baseball_image, (67, 60))

projectile_image = pygame.image.load('ball.png').convert_alpha()
projectile_image = pygame.transform.scale(projectile_image, (25, 25))

background_image = pygame.image.load('background.png').convert_alpha()
background_image = pygame.transform.scale(background_image, (1280, 720))

other_background_image = pygame.image.load('background2.png').convert_alpha()
other_background_image = pygame.transform.scale(other_background_image, (1280, 720))

glove_image = pygame.image.load('glove.png').convert_alpha()
glove_image = pygame.transform.scale(glove_image, (100, 100))

# Colors
black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
white = (255, 255, 255)
purple = (139, 0, 139)
gray = (211, 211, 211)

# Fonts
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 60)