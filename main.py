import pygame as pg
from pygame import mixer
import pygame.freetype as freetype

import sys
import random
import math
import datetime
import pickle
import os
import itertools
import webbrowser

#iInitialize all imported pygame modules
pg.init()

info = pg.display.Info()
screen_width = info.current_w #1536, Without dpi awareness
screen_height = info.current_h #864

#Initial window dimensions
if screen_width >= 1536:
    window_width, window_height = 1280, 720
else:
    window_width, window_height = 1152, 648

#Pygame window
flags = pg.RESIZABLE #| pg.FULLSCREEN
window  = pg.display.set_mode((window_width, window_height), flags)
window_rect = window.get_rect()

#Setting window title bar properties
pg.display.set_caption('Space Overkill')
icon = pg.image.load('.\\resources\\images\\player\\battleship32.png')
pg.display.set_icon(icon)

#Loading and playing game music
mixer.music.load(r'.\resources\sounds\background1-short.wav')
mixer.music.play(-1)
#print(mixer.music.get_volume())#0.9921875
mixer.music.set_volume(0.70)

#Setting different sound channels for simultaneous playback
num_channels = 10
mixer.set_num_channels(num_channels)
channels = []

for i in range(num_channels): 
    channels.append(mixer.Channel(i))


#Loading Screen
window.fill((255,255,255))
background_img = pg.image.load('.\\resources\\images\\background\\background.png').convert_alpha()
background_over = pg.image.load(r'.\resources\images\text-background\game-intro.png').convert_alpha()
load_font = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Bold.ttf', 120)
load_text = load_font.render('Loading'.upper(), True, (0,0,0))
load_text_rect = load_text.get_rect(center=(window_width/2, window_height/2))
window.blit(background_img, (0,0))
window.blit(background_over, (0,0))
window.blit(load_text, load_text_rect)
pg.display.update()


#Reading highscore file
try:
    with open('highscores.pickle', 'rb') as fh:
        hs_dict = pickle.load(fh)
except FileNotFoundError:
    hs_dict = {}

#Player properties and functions
player_img = pg.image.load('.\\resources\\images\\player\\battleship100.png').convert_alpha()
player_img_size = player_img_w, player_img_h = player_img.get_size()
player_rect = player_img.get_rect()
playerX = window_width/2 - player_img_w/2
playerY = ((window_height/player_img_h)-1.5)*player_img_h
#Here constant(1.5) represent the padding of player image from bottom of
#window in terms(multiple) of player image height 
playerX_change = 0
playerY_change = 0
cur_player_x = playerX + playerX_change
cur_player_y = playerY + playerY_change
player_rect.x = cur_player_x
player_rect.y = cur_player_y

player_xspeed = 0.7
player_yspeed = 0.5

player_max_health = 5
player_health = player_max_health
player_health_img1 = pg.image.load('.\\resources\\images\\player\\heart-fill32.png')
player_health_img2 = pg.image.load('.\\resources\\images\\player\\heart-empty32.png')
player_health_rects = []

def update_player_health_rect():
    global window_width, player_health_rects

    player_health_rects.clear()
    
    start = (window_width/2) - (((player_max_health-1)*42)+32)/2

    for i in range(player_max_health):
        player_health_rects.append(pg.Rect(start+42*i, 10, 32, 32))

update_player_health_rect()

def draw_player():#xchange, ychange
    global player_img , player_img_size, player_img_w, player_img_h, player_rect
    global playerX, playerY, playerX_change, playerY_change, cur_player_x, cur_player_y

    cur_player_x += playerX_change
    cur_player_y += playerY_change
    
    #Setting player boundaries
    if cur_player_x <= 2:
        cur_player_x = 2
    elif cur_player_x >= window_width-player_img_w-2:
        cur_player_x = window_width-player_img_w-2
        
    if cur_player_y <= ((window_height/player_img_h)-3)*player_img_h:
        cur_player_y = ((window_height/player_img_h)-3)*player_img_h
    elif cur_player_y >= window_height-player_img_h-2:
        cur_player_y = window_height-player_img_w-2

    player_rect.x = cur_player_x
    player_rect.y = cur_player_y
    
    window.blit(player_img, (cur_player_x, cur_player_y))

    for i, rect in zip(range(player_health), player_health_rects):
        window.blit(player_health_img1, rect)

    for i, rect in zip(range(player_max_health-player_health), player_health_rects[::-1]):
        window.blit(player_health_img2, rect)

def player_update(event):
    global cur_player_x, cur_player_y, player_rect, window_width, window_height

    player_rect.center = (event.w/window_width*player_rect.centerx,
                                  event.h/window_height*player_rect.centery)
    cur_player_x, cur_player_y = player_rect.left, player_rect.top

    if powerups.pcollected == 'freeze':
        powerups.powerups['freeze']['rect'].center = player_rect.center


#Small enemy properties and functions
num_enemy_small = 8
enemy_small_img = pg.image.load('.\\resources\\images\\enemy\\aircraft80.png').convert_alpha()
enemy_small_img_size = enemy_small_img_w, enemy_small_img_h = enemy_small_img.get_size()
enemy_small_xspeed = 0.5
enemy_small_yspeed = 0.1
enemy_small = {}

enemy_small_laser = pg.image.load('.\\resources\\images\\enemy\\minus(90)9x24.png')
enemy_small_laser_xspeed = 0
enemy_small_laser_yspeed = 0.5
enemy_small_laser_sound = mixer.Sound(r'.\resources\sounds\laser3.wav')
enemy_small_killed = 0

#Dict to hold only thhose enemies which are visible on screen. This is used to draw small enemies
#when its time to spawn medium/large enemy on reaching particular score
enemy_small_last = {}

explosion_img = [pg.image.load(r'.\resources\images\enemy\explosion80.png').convert_alpha(),
                 pg.image.load(r'.\resources\images\enemy\explosion(1)80.png').convert_alpha()]


def init_enemy_small_img():
    global enemy_small, enemy_small_img
    
    for i in range(1, num_enemy_small+1):
        enemy_small['enemy'+str(i)] = {}
        enemy_small['enemy'+str(i)]['img'] = enemy_small_img #pg.image.load('.\\resources\\images\\enemy\\aircraft80.png')
        enemy_small['enemy'+str(i)]['rect'] = enemy_small['enemy'+str(i)]['img'].get_rect()
    
def init_enemy_small_pos():
    global enemy_small, num_enemy_small, enemy_small_xspeed, enemy_small_yspeed
    global window_width, enemy_small_img_w, enemy_small_laser

    for i in range(1, num_enemy_small+1):
        enemy_small['enemy'+str(i)]['enemy_smallX_change'] = random.choice([enemy_small_xspeed, -enemy_small_xspeed])
        enemy_small['enemy'+str(i)]['enemy_smallY_change'] = enemy_small_yspeed
        enemy_small['enemy'+str(i)]['cur_enemy_small_x'] = random.randint(2, window_width-enemy_small_img_w-2)
        enemy_small['enemy'+str(i)]['cur_enemy_small_y'] = -300 - (120 * (i-1))
        enemy_small['enemy'+str(i)]['rect'].x = enemy_small['enemy'+str(i)]['cur_enemy_small_x']
        enemy_small['enemy'+str(i)]['rect'].y = enemy_small['enemy'+str(i)]['cur_enemy_small_y']
        enemy_small['enemy'+str(i)]['alive'] = True
        enemy_small['enemy'+str(i)]['explosion_time'] = 60
        enemy_small['enemy'+str(i)]['laser_draw'] = False
        enemy_small['enemy'+str(i)]['laser_rect'] = enemy_small_laser.get_rect()

    #print(enemy_small)

init_enemy_small_img()
init_enemy_small_pos()

def draw_enemy_small(dt=1):
    global enemy_small, enemy_small_xspeed, enemy_small_yspeed, lvl_value
    global powerups, enemy_small_laser_sound, channels

    for enemy in enemy_small:
        if powerups.pcollected != 'freeze':
            if enemy_small[enemy]['cur_enemy_small_x'] <= 2:
                enemy_small[enemy]['enemy_smallX_change'] = enemy_small_xspeed
                enemy_small[enemy]['enemy_smallY_change'] = enemy_small_yspeed
            elif enemy_small[enemy]['cur_enemy_small_x'] >= window_width - enemy_small_img_w - 2:
                enemy_small[enemy]['enemy_smallX_change'] = -enemy_small_xspeed
                enemy_small[enemy]['enemy_smallY_change'] = enemy_small_yspeed
            
        enemy_small[enemy]['cur_enemy_small_x'] += enemy_small[enemy]['enemy_smallX_change']*dt
        enemy_small[enemy]['cur_enemy_small_y'] += enemy_small[enemy]['enemy_smallY_change']*dt

        enemy_small[enemy]['rect'].x = enemy_small[enemy]['cur_enemy_small_x']
        enemy_small[enemy]['rect'].y = enemy_small[enemy]['cur_enemy_small_y']

        #Drawing enemy if alive else drawing explosion if destroyed and resetting the enemy properties
        if (enemy_small[enemy]['rect'].y < window_height+10) and enemy_small[enemy]['alive']:
            window.blit(enemy_small[enemy]['img'],
                        (enemy_small[enemy]['cur_enemy_small_x'],
                         enemy_small[enemy]['cur_enemy_small_y']))
            if lvl_value > 9 and 0 <= enemy_small[enemy]['rect'].y <= window_height/2-100:
                if powerups.pcollected == 'freeze':
                    ch = 0
                else:
                    ch = random.choices([0, 1], [19, 1], k=1)[0]
                #print(ch)
                if ch and not enemy_small[enemy]['laser_draw']:
                    enemy_small[enemy]['laser_draw'] = True
                    enemy_small[enemy]['laser_rect'].midtop = enemy_small[enemy]['rect'].center
                    channels[0].play(enemy_small_laser_sound)
                    
        elif (enemy_small[enemy]['rect'].y < window_height+10 and
              not enemy_small[enemy]['alive'] and
              enemy_small[enemy]['explosion_time'] > 0):
            if 0 <= enemy_small[enemy]['explosion_time'] < 15 or 30 <= enemy_small[enemy]['explosion_time'] < 45:
                window.blit(explosion_img[1],
                            (enemy_small[enemy]['cur_enemy_small_x'],
                             enemy_small[enemy]['cur_enemy_small_y']))
            elif 15 <= enemy_small[enemy]['explosion_time'] < 30 or 45 <= enemy_small[enemy]['explosion_time'] <= 60:
                window.blit(explosion_img[0],
                            (enemy_small[enemy]['cur_enemy_small_x'],
                             enemy_small[enemy]['cur_enemy_small_y']))
            enemy_small[enemy]['explosion_time'] -= 1
        elif (enemy_small[enemy]['rect'].y >= window_height+10):
            i = int(enemy[5:])
            enemy_small['enemy'+str(i)]['enemy_smallX_change'] = random.choice([enemy_small_xspeed, -enemy_small_xspeed])
            enemy_small['enemy'+str(i)]['enemy_smallY_change'] = enemy_small_yspeed
            enemy_small['enemy'+str(i)]['cur_enemy_small_x'] = random.randint(2, window_width-enemy_small_img_w-2)
            enemy_small['enemy'+str(i)]['cur_enemy_small_y'] = -300 #- (90 * (i-1))
            enemy_small['enemy'+str(i)]['rect'].x = enemy_small['enemy'+str(i)]['cur_enemy_small_x']
            enemy_small['enemy'+str(i)]['rect'].y = enemy_small['enemy'+str(i)]['cur_enemy_small_y']
            enemy_small['enemy'+str(i)]['alive'] = True
            enemy_small['enemy'+str(i)]['explosion_time'] = 60

    draw_enemy_small_laser(dt)

def draw_enemy_small_laser(dt=1):
    global enemy_small, enemy_small_laser_xspeed, enemy_small_laser_yspeed
    global enemy_small_laser, window_height

    del_list = []
    
    for enemy in enemy_small:

        if enemy_small[enemy]['laser_draw']:
            window.blit(enemy_small_laser, enemy_small[enemy]['laser_rect'])
            #print(enemy_small_laser_yspeed * dt)
            enemy_small[enemy]['laser_rect'].y += enemy_small_laser_yspeed * dt

            if enemy_small[enemy]['laser_rect'].bottom > window_height+50:
                del_list.append(enemy)
        #if enemy == 'enemy1':
            #print(enemy_small[enemy]['laser_rect'])

    for enemy in del_list:
        enemy_small[enemy]['laser_draw'] = False
        enemy_small[enemy]['laser_rect'].topleft = (0,0)
            

def draw_enemy_small_last(dt=1):
    global enemy_small_last, enemy_small_xspeed, enemy_small_yspeed
    global spawn_medium_enemy_trigger2, spawn_large_enemy_trigger2
    global enemy_small_laser_sound, channels

    del_list = []

    for enemy in enemy_small_last:
        if powerups.pcollected != 'freeze':
            if enemy_small_last[enemy]['rect'].x <= 2:
                enemy_small_last[enemy]['enemy_smallX_change'] = enemy_small_xspeed
                enemy_small_last[enemy]['enemy_smallY_change'] = enemy_small_yspeed
            elif enemy_small_last[enemy]['rect'].x >= window_width-enemy_small_img_w-2:
                enemy_small_last[enemy]['enemy_smallX_change'] = -enemy_small_xspeed
                enemy_small_last[enemy]['enemy_smallY_change'] = enemy_small_yspeed
    
        enemy_small_last[enemy]['cur_enemy_small_x'] += enemy_small_last[enemy]['enemy_smallX_change']*dt
        enemy_small_last[enemy]['cur_enemy_small_y'] += enemy_small_last[enemy]['enemy_smallY_change']*dt

        enemy_small_last[enemy]['rect'].x = enemy_small_last[enemy]['cur_enemy_small_x']
        enemy_small_last[enemy]['rect'].y = enemy_small_last[enemy]['cur_enemy_small_y']
        
        if (enemy_small_last[enemy]['rect'].y < window_height+10) and enemy_small_last[enemy]['alive']:
            window.blit(enemy_small_last[enemy]['img'],
                        (enemy_small_last[enemy]['cur_enemy_small_x'],
                         enemy_small_last[enemy]['cur_enemy_small_y']))
            if lvl_value > 9 and 0 <= enemy_small_last[enemy]['rect'].y <= window_height/2-100:
                if powerups.pcollected == 'freeze':
                    ch = 0
                else:
                    ch = random.choices([0, 1], [19, 1], k=1)[0]
                #print(ch)
                if ch and not enemy_small_last[enemy]['laser_draw']:
                    enemy_small_last[enemy]['laser_draw'] = True
                    enemy_small_last[enemy]['laser_rect'].midtop = enemy_small[enemy]['rect'].center
                    channels[0].play(enemy_small_laser_sound)
                    
        elif (enemy_small_last[enemy]['rect'].y < window_height+10 and
              not enemy_small_last[enemy]['alive'] and
              enemy_small_last[enemy]['explosion_time'] > 0):
            if 0 <= enemy_small_last[enemy]['explosion_time'] < 15 or 30 <= enemy_small_last[enemy]['explosion_time'] < 45:
                window.blit(explosion_img[1],
                            (enemy_small_last[enemy]['cur_enemy_small_x'],
                             enemy_small_last[enemy]['cur_enemy_small_y']))
            elif 15 <= enemy_small_last[enemy]['explosion_time'] < 30 or 45 <= enemy_small_last[enemy]['explosion_time'] < 60:
                window.blit(explosion_img[0],
                            (enemy_small_last[enemy]['cur_enemy_small_x'],
                             enemy_small_last[enemy]['cur_enemy_small_y']))
            enemy_small_last[enemy]['explosion_time'] -= 1
        elif (enemy_small_last[enemy]['rect'].y >= window_height+10):
            del_list.append(enemy)

    for enemy in del_list:
        del enemy_small_last[enemy]

    draw_enemy_small_laser(dt)

    if not enemy_small_last:
        pg.time.set_timer(enemy_medium.enemy_flash, 300)
        pg.time.set_timer(enemy_medium.laser_event, enemy_medium.laser_delay)

        pg.time.set_timer(enemy_large.enemy_flash, 300)
        pg.time.set_timer(enemy_large.laser_event, enemy_large.laser_delay)

        spawn_medium_enemy_trigger2 = True
        spawn_large_enemy_trigger2 = True

def init_enemy_small_last():
    global enemy_small, enemy_small_last

    for enemy in enemy_small:
        #if (0 <= enemy_small[enemy]['cur_enemy_small_x'] <= window_width and
         #   -enemy_small[enemy]['rect'].height <= enemy_small[enemy]['cur_enemy_small_y'] <= window_height):
        if window_rect.colliderect(enemy_small[enemy]['rect']):
            enemy_small_last[enemy] = enemy_small[enemy]

#Triggers/Flags to spawn medium enemy
spawn_medium_enemy_trigger1 = False
isinit_enemy_small_last = False
spawn_medium_enemy_trigger2 = False


#Medium enemy properties and functions
class EnemyMedium():
    def __init__(self):
        self.enemy_img = pg.image.load('.\\resources\\images\\enemy\\enemy-medium(180)160.png').convert_alpha()
        self.enemy_rect_pos = [(window_width*4/8, 200), (window_width*1/8, 200),
                               (window_width*4/8, 200), (window_width*7/8, 200)]
        self.new_pos_acquired = False
        self.new_pos_set = False
        self.timer = False
        self.time_elapsed = 0
        self.pos_i = 0
        self.enemy_health = 20

        self.laser_img1 = pg.image.load('.\\resources\\images\\enemy\\minus(tilt1)9x24.png').convert_alpha()
        self.laser_img2 = pg.image.load('.\\resources\\images\\enemy\\minus(tilt2)9x24.png').convert_alpha()
        self.laser_yspeed = 0.5
        self.laser_xspeed = 0.5*(21/300)
        self.laser_n = 1
        self.lasers = {}
        self.laser_clock = pg.time.Clock()
        self.LL = 0
        self.UL = 3000
        self.DIFF = 6000
        self.set_laser_timer_lim = False
        self.laser_time = 0
        self.laser_delay = 1000
        self.laser_pause = 5000
        self.laser_event = pg.USEREVENT + 1
        self.laser_sound = mixer.Sound(r'.\resources\sounds\laser3.wav')

        self.enemy_clock = pg.time.Clock()

        self.empty_img = pg.image.load('.\\resources\\images\\enemy\\empty160.png').convert_alpha()
        self.flash_surface = self.enemy_img
        self.enemy_flash = pg.USEREVENT + 2
        self.num_flash = 0

        self.set_params()

    def set_params(self):
        self.enemy_rect = self.enemy_img.get_rect()
        self.enemy_rect.center = (window_width/2, -200)
        self.enemyX = self.enemy_rect.x
        self.enemyY = self.enemy_rect.y
        self.enemy_xspeed = 0.5
        self.enemy_yspeed = 0.4
        self.enemy_xchange = 0
        self.enemy_ychange = 0
        self.cur_enemy_x = self.enemy_rect.x
        self.cur_enemy_y = self.enemy_rect.y
        self.laser_sound.set_volume(0.8)

        pg.time.set_timer(self.enemy_flash, 300)
        pg.time.set_timer(self.laser_event, self.laser_delay)

    def resize(self):
        global spawn_medium_enemy_trigger2
        
        self.enemy_rect_pos = [(window_width*4/8, 200), (window_width*1/8, 200),
                               (window_width*4/8, 200), (window_width*7/8, 200)]

        if spawn_medium_enemy_trigger2 == False:
            self.enemy_rect.center = (window_width/2, -200)
            self.cur_enemy_x = self.enemy_rect.x
            self.cur_enemy_y = self.enemy_rect.y
        

    def add_laser(self):
        global mute, channels
        
        if mute == False:
            channels[0].play(self.laser_sound)

        if self.laser_n > 7:
            #pg.time.set_timer(self.laser_event, self.laser_pause)
            self.laser_n = 1

        self.lasers['laser'+str(self.laser_n)] = {}
        self.lasers['laser'+str(self.laser_n)]['img1'] = self.laser_img1
        self.lasers['laser'+str(self.laser_n)]['img2'] = self.laser_img2
        self.lasers['laser'+str(self.laser_n)]['laserY_change'] = 0
        self.lasers['laser'+str(self.laser_n)]['laserX_change'] = 0
        self.lasers['laser'+str(self.laser_n)]['laser1rect'] = self.laser_img1.get_rect()
        self.lasers['laser'+str(self.laser_n)]['laser2rect'] = self.laser_img2.get_rect()
        self.lasers['laser'+str(self.laser_n)]['laser1rect'].midtop = (self.enemy_rect.midbottom[0]-28, self.enemy_rect.midbottom[1])
        self.lasers['laser'+str(self.laser_n)]['laser2rect'].midtop = (self.enemy_rect.midbottom[0]+27, self.enemy_rect.midbottom[1])
        self.lasers['laser'+str(self.laser_n)]['cur_laser1_y'] = self.lasers['laser'+str(self.laser_n)]['laser1rect'].y
        self.lasers['laser'+str(self.laser_n)]['cur_laser2_y'] = self.lasers['laser'+str(self.laser_n)]['laser2rect'].y
        self.lasers['laser'+str(self.laser_n)]['cur_laser1_x'] = self.lasers['laser'+str(self.laser_n)]['laser1rect'].x
        self.lasers['laser'+str(self.laser_n)]['cur_laser2_x'] = self.lasers['laser'+str(self.laser_n)]['laser2rect'].x
        self.lasers['laser'+str(self.laser_n)]['laser1draw'] = True
        self.lasers['laser'+str(self.laser_n)]['laser2draw'] = True
        #print(self.lasers['laser'+str(self.laser_n)]['laser1rect'].midtop)
        #print(self.lasers['laser'+str(self.laser_n)]['laser2rect'].midtop)
        
        self.laser_n += 1

    def draw_laser(self, dt):
        global player_rect
        
        delete = []
        for laser in self.lasers:
            if (self.lasers[laser]['laser1rect'].top >= window_height+5 and
                self.lasers[laser]['laser2rect'].top >= window_height+5):
                delete.append(laser)
                continue

            self.lasers[laser]['laserY_change'] = self.laser_yspeed*dt
            self.lasers[laser]['laserX_change'] = self.laser_xspeed*dt

            if (self.lasers[laser]['laser1rect'].colliderect(player_rect) and
                self.lasers[laser]['laser1draw']):
                #self.lasers[laser]['laser1rect'].x = self.lasers[laser]['laser1rect'].y = -50
                self.lasers[laser]['laser1draw'] = False
                #print('hit')
            if (self.lasers[laser]['laser2rect'].colliderect(player_rect) and
                self.lasers[laser]['laser2draw']):
                #self.lasers[laser]['laser2rect'].x = self.lasers[laser]['laser2rect'].y = -50
                self.lasers[laser]['laser2draw'] = False
                #print('hit')
            
            self.lasers[laser]['cur_laser1_y'] += self.lasers[laser]['laserY_change']
            self.lasers[laser]['cur_laser2_y'] += self.lasers[laser]['laserY_change']
            self.lasers[laser]['laser1rect'].y = self.lasers[laser]['cur_laser1_y']
            self.lasers[laser]['laser2rect'].y = self.lasers[laser]['cur_laser2_y']
            self.lasers[laser]['cur_laser1_x'] -= self.lasers[laser]['laserX_change']
            self.lasers[laser]['cur_laser2_x'] += self.lasers[laser]['laserX_change']
            self.lasers[laser]['laser1rect'].x = self.lasers[laser]['cur_laser1_x']
            self.lasers[laser]['laser2rect'].x = self.lasers[laser]['cur_laser2_x']
            
            L1x = self.lasers[laser]['cur_laser1_x']
            L1y = self.lasers[laser]['cur_laser1_y']
            L2x = self.lasers[laser]['cur_laser2_x']
            L2y = self.lasers[laser]['cur_laser2_y']

            #print(L1x, L1y)
            #print(L2x, L2y)

            if self.lasers[laser]['laser1draw']:
                window.blit(self.lasers[laser]['img1'], (L1x, L1y))
            if self.lasers[laser]['laser2draw']:
                window.blit(self.lasers[laser]['img2'], (L2x, L2y))

        #print(delete)
        for key in delete:
            del self.lasers[key]

    def draw_enemy(self, dt, event_list):
        global powerups

        #print(self.pos_i)
        new_enemy_pos = self.enemy_rect_pos[self.pos_i]
        #print(self.enemy_rect.center, new_enemy_pos)
        #pg.time.set_timer(self.laser_event, self.laser_delay)

        if not self.new_pos_set and self.enemy_health > 0:

            if (math.fabs(self.enemy_rect.centerx-new_enemy_pos[0]) > 5 or
                math.fabs(self.enemy_rect.centery-new_enemy_pos[1]) > 5):
                if self.enemy_rect.center[0] - new_enemy_pos[0] > 5:
                    self.cur_enemy_x += -self.enemy_xspeed*dt
                elif self.enemy_rect.center[0] - new_enemy_pos[0] < -5:
                    self.cur_enemy_x += self.enemy_xspeed*dt
                if self.enemy_rect.center[1] < 200:
                    self.cur_enemy_y += self.enemy_yspeed*dt
                self.enemy_rect.x = self.cur_enemy_x
                self.enemy_rect.y = self.cur_enemy_y

            else:
                #self.laser_time = 0
                #pg.time.set_timer(self.laser_event, self.laser_delay)
                #self.new_pos_acquired = True
                self.new_pos_set = True
                #self.timer = True
                self.time_elapsed = 0
                #self.enemy_clock.tick()

        elif self.new_pos_set and self.enemy_health > 0:
            self.enemy_rect.centerx, self.enemy_rect.centery = new_enemy_pos
            self.cur_enemy_x = self.enemy_rect.x
            self.cur_enemy_y = self.enemy_rect.y

        if self.enemy_health > 0:
            window.blit(self.enemy_img,
                        (self.cur_enemy_x, self.cur_enemy_y))
        else:
            for event in event_list:
                if event.type == self.enemy_flash:
                    self.flash_surface = self.enemy_img if self.flash_surface == self.empty_img else self.empty_img
            window.blit(self.flash_surface,
                        (self.cur_enemy_x, self.cur_enemy_y))
                    

        #if self.timer:
        if self.new_pos_set:
            self.time_elapsed += dt#self.enemy_clock.tick()

        if self.time_elapsed >= 3000:
            if self.pos_i == len(self.enemy_rect_pos)-1:
                self.pos_i = 0
            else:
                self.pos_i += 1
                
            self.new_pos_set = False
            #self.timer = False
            self.time_elapsed = 0

        '''
        self.laser_time += self.laser_clock.tick()
        
        if self.LL <= self.laser_time <= self.UL:
            #print(self.LL, self.laser_time, self.UL)
            self.add_laser()
            self.draw_laser(dt)
            self.set_laser_timer_lim = True
        #elif self.set_laser_timer_lim:
         #   self.LL += self.DIFF
          #  self.UL += self.DIFF
           # self.set_laser_timer_lim = False
        '''

        if self.enemy_health > 0 and powerups.pcollected != 'freeze':
            for event in event_list:
                if event.type == self.laser_event:
                    self.add_laser()
            self.draw_laser(dt)

        self.check_health(event_list)

    def check_health(self, event_list):
        global score_value, spawn_medium_enemy_trigger1, spawn_large_enemy_trigger1
        global spawn_medium_enemy_trigger2, isinit_enemy_small_last, spawn_large_enemy_trigger2
        global enemy_small_killed

        if self.enemy_health <= 0:
            self.lasers.clear()
        
        if self.enemy_health <= 0:
            for event in event_list:
                if event.type == self.enemy_flash:
                    self.num_flash += 1
            if self.num_flash >= 12:
                score_value += 10
                spawn_medium_enemy_trigger1 = False
                spawn_medium_enemy_trigger2 = False
                spawn_large_enemy_trigger1 = False
                spawn_large_enemy_trigger2 = False
                isinit_enemy_small_last = False
                self.__init__()
                init_enemy_small_pos()
                increase_lvl()
                pg.time.set_timer(self.enemy_flash, 0)
                pg.time.set_timer(self.laser_event, 0)
                enemy_small_killed = 0
            
enemy_medium = EnemyMedium()


#Large enemy properties and functions
class EnemyLarge():
    def __init__(self):
        self.enemy_img = pg.image.load('.\\resources\\images\\enemy\\enemy-large200.png').convert_alpha()
        #self.enemy_rect_pos = [(window_width*4/8, 200), (window_width*1/8, 200),
         #                      (window_width*4/8, 200), (window_width*7/8, 200)]
        #self.new_pos_acquired = False
        #self.new_pos_set = False
        #self.timer = False
        #self.time_elapsed = 0
        #self.pos_i = 0
        self.enemy_health = 40

        self.laser_img = pg.image.load('.\\resources\\images\\enemy\\minus(90)9x24.png').convert_alpha()
        self.laser_yspeed = 0.6
        self.laser_n = 1
        self.lasers = {}
        self.lasers_draw = False
        self.laser_delay = 300
        #self.laser_pause = 5000
        self.laser_event = pg.USEREVENT + 3
        self.laser_sound = mixer.Sound(r'.\resources\sounds\laser3.wav')

        self.plasma_img = pg.image.load('.\\resources\\images\\enemy\\plasma-ball360(2).png').convert_alpha()
        self.plasma_yspeed = 0.4
        self.plasma_xspeed = 0.1
        #self.laser_n = 1
        self.plasmas = {}
        self.plasmas_draw = True
        #self.laser_delay = 700
        #self.laser_pause = 5000
        #self.laser_event = pg.USEREVENT + 1
        self.plasma_sound = mixer.Sound(r'.\resources\sounds\electrical-shock-zap-short.wav')

        self.enemy_clock = pg.time.Clock()

        self.empty_img = pg.image.load('.\\resources\\images\\enemy\\empty160.png')
        self.flash_surface = self.enemy_img
        self.enemy_flash = pg.USEREVENT + 4
        self.num_flash = 0

        self.enemy_angle = 0
        self.rotate_enemy_event = pg.USEREVENT + 5
        self.rotate_delay = 10000

        self.weapon = 'plasma'

        self.set_params()

    def set_params(self):
        self.enemy_rect = self.enemy_img.get_rect()
        self.enemy_rect.center = (window_width/2, -200)
        self.enemy_xspeed = 0#0.5
        self.enemy_yspeed = 0#0.3
        self.set_enemy_speed = True
        self.enemy_xchange = 0
        self.enemy_ychange = 0
        self.cur_enemy_x = self.enemy_rect.x
        self.cur_enemy_y = self.enemy_rect.y
        self.rot_enemy = self.enemy_img
        self.rot_enemy_rect = self.enemy_rect.copy()
        self.plasma_sound.set_volume(0.3)
        self.laser_sound.set_volume(0.8)

        pg.time.set_timer(self.enemy_flash, 300)
        pg.time.set_timer(self.laser_event, self.laser_delay)
        #pg.time.set_timer(self.rotate_enemy_event, self.rotate_delay)

        self.set_plasma()

    def resize(self):
        global spawn_large_enemy_trigger2

        if spawn_large_enemy_trigger2 == False:
            self.enemy_rect.center = (window_width/2, -200)
        
    def add_laser(self):
        global mute, channels
        
        if mute == False:
            channels[0].play(self.laser_sound)

        if self.laser_n > 7:
            #pg.time.set_timer(self.laser_event, self.laser_pause)
            self.laser_n = 1

        self.lasers['laser'+str(self.laser_n)] = {}
        self.lasers['laser'+str(self.laser_n)]['img'] = self.laser_img
        self.lasers['laser'+str(self.laser_n)]['laserY_change'] = 0
        self.lasers['laser'+str(self.laser_n)]['laser1rect'] = self.laser_img.get_rect()
        #self.lasers['laser'+str(self.laser_n)]['laser2rect'] = self.laser_img.get_rect()
        self.lasers['laser'+str(self.laser_n)]['laser1rect'].midtop = (self.enemy_rect.right-65, self.enemy_rect.bottom)
        #self.lasers['laser'+str(self.laser_n)]['laser2rect'].midtop = (self.enemy_rect.midbottom[0]+27, self.enemy_rect.midbottom[1])
        self.lasers['laser'+str(self.laser_n)]['cur_laser1_y'] = self.lasers['laser'+str(self.laser_n)]['laser1rect'].y
        #self.lasers['laser'+str(self.laser_n)]['cur_laser2_y'] = self.lasers['laser'+str(self.laser_n)]['laser2rect'].y
        self.lasers['laser'+str(self.laser_n)]['laser1draw'] = True
        #self.lasers['laser'+str(self.laser_n)]['laser2draw'] = True
        #print(self.lasers['laser'+str(self.laser_n)]['laser1rect'].midtop)
        #print(self.lasers['laser'+str(self.laser_n)]['laser2rect'].midtop)
        
        self.laser_n += 1

    def draw_laser(self, dt):
        global player_rect
        
        delete = []
        for laser in self.lasers:
            if self.lasers[laser]['laser1rect'].top >= window_height+5:
                delete.append(laser)
                continue

            self.lasers[laser]['laserY_change'] = self.laser_yspeed*dt

            if (self.lasers[laser]['laser1rect'].colliderect(player_rect) and
                self.lasers[laser]['laser1draw']):
                #self.lasers[laser]['laser1rect'].x = self.lasers[laser]['laser1rect'].y = -50
                self.lasers[laser]['laser1draw'] = False
                #print('hit')
            
            self.lasers[laser]['cur_laser1_y'] += self.lasers[laser]['laserY_change']
            self.lasers[laser]['laser1rect'].y = self.lasers[laser]['cur_laser1_y']
            L1x = self.lasers[laser]['laser1rect'].x
            L1y = self.lasers[laser]['cur_laser1_y']

            #print(L1x, L1y)
            #print(L2x, L2y)

            if self.lasers[laser]['laser1draw']:
                window.blit(self.lasers[laser]['img'], (L1x, L1y))

        #print(delete)
        for key in delete:
            del self.lasers[key]

    def set_plasma(self):
        self.plasmas = {
            'plasma1' : {
                'Xchange' : -self.plasma_xspeed*1.2,
                'Ychange' : self.plasma_yspeed,
                'rect' : self.plasma_img.get_rect(w=16, h=16, midtop=(self.enemy_rect.left+62, self.enemy_rect.bottom)),
                #'cur_x' : self.plasmas['plasma1']['rect'].x,
                #'cur_y' : self.plasmas['plasma1']['rect'].y,
                'draw' : True,
                'pixel_travel' : 0,
                'scale' : 0.0444,
                'angle' : 0},
            'plasma2' : {
                'Xchange' : -self.plasma_xspeed/2,
                'Ychange' : self.plasma_yspeed,
                #'rect' : self.plasma_img.get_rect(w=16, h=16, center=(self.plasmas['plasma1']['rect'].centerx+25,
                 #                                 self.plasmas['plasma1']['rect'].centery)),
                #'cur_x' : self.plasmas['plasma1']['rect'].x,
                #'cur_y' : self.plasmas['plasma1']['rect'].y,
                'draw' : True,
                'pixel_travel' : 0,
                'scale' : 0.0444,
                'angle' : 0},
            'plasma3' : {
                'Xchange' : self.plasma_xspeed/2,
                'Ychange' : self.plasma_yspeed,
                #'rect' : self.plasma_img.get_rect(w=16, h=16, center=(self.plasmas['plasma2']['rect'].centerx+25,
                 #                                 self.plasmas['plasma1']['rect'].centery)),
                #'cur_x' : self.plasmas['plasma1']['rect'].x,
                #'cur_y' : self.plasmas['plasma1']['rect'].y,
                'draw' : True,
                'pixel_travel' : 0,
                'scale' : 0.0444,
                'angle' : 0},
            'plasma4' : {
                'Xchange' : self.plasma_xspeed*1.2,
                'Ychange' : self.plasma_yspeed,
                #'rect' : self.plasma_img.get_rect(w=16, h=16, center=(self.plasmas['plasma3']['rect'].centerx+25,
                 #                                 self.plasmas['plasma1']['rect'].centery)),
                #'cur_x' : self.plasmas['plasma1']['rect'].x,
                #'cur_y' : self.plasmas['plasma1']['rect'].y,
                'draw' : True,
                'pixel_travel' : 0,
                'scale' : 0.0444,
                'angle' : 0}
            }

        for plasma in self.plasmas:
            if plasma != 'plasma1':
                prev_plasma = 'plasma'+str(int(plasma[-1])-1)
                self.plasmas[plasma]['rect'] = self.plasma_img.get_rect(w=16, h=16,
                                                                        center=(self.plasmas[prev_plasma]['rect'].centerx+25,
                                                                                self.plasmas[prev_plasma]['rect'].centery))
            self.plasmas[plasma]['cur_x'] = self.plasmas[plasma]['rect'].x
            self.plasmas[plasma]['cur_y'] = self.plasmas[plasma]['rect'].y
        
    def draw_plasma(self, dt):
        global player_rect, mute, channels

        #if self.plasmas['plasma1']['rect'].midtop == (self.enemy_rect.left+62, self.enemy_rect.bottom):
        if self.plasmas['plasma1']['rect'].top == self.enemy_rect.bottom:
            if mute == False:
                channels[2].play(self.plasma_sound)
        
        for plasma in self.plasmas:
            if self.plasmas[plasma]['rect'].top >= window_height+10:
                self.set_plasma()
                #if mute == False:
                 #   self.plasma_sound.play()
                break

            #self.plasmas[plasma]['Xchange'] = self.plasma_xspeed*dt
            #self.plasmas[plasma]['Ychange'] = self.plasma_yspeed*dt

            self.plasmas[plasma]['cur_x'] += self.plasmas[plasma]['Xchange']*dt
            self.plasmas[plasma]['cur_y'] += self.plasmas[plasma]['Ychange']*dt

            self.plasmas[plasma]['rect'].w = self.plasma_img.get_width()*self.plasmas[plasma]['scale']
            self.plasmas[plasma]['rect'].h = self.plasma_img.get_height()*self.plasmas[plasma]['scale']
            self.plasmas[plasma]['rect'].x = self.plasmas[plasma]['cur_x']
            self.plasmas[plasma]['rect'].y = self.plasmas[plasma]['cur_y']

            if (self.plasmas[plasma]['rect'].colliderect(player_rect) and
                self.plasmas[plasma]['draw']):
                self.plasmas[plasma]['draw'] = False

            Px = self.plasmas[plasma]['cur_x']
            Py = self.plasmas[plasma]['cur_y']

            P_surface = pg.transform.rotozoom(self.plasma_img,
                                              self.plasmas[plasma]['angle'],
                                              self.plasmas[plasma]['scale'])
            
            if self.plasmas[plasma]['draw']:
                window.blit(P_surface, self.plasmas[plasma]['rect'])#(Px, Py)

            self.plasmas[plasma]['pixel_travel'] += self.plasmas[plasma]['cur_y']
            if self.plasmas[plasma]['pixel_travel'] >= 10:
                self.plasmas[plasma]['pixel_travel'] = 0
                if self.plasmas[plasma]['rect'].bottom <= window_height-200:
                    self.plasmas[plasma]['scale'] += 0.0015

            self.plasmas[plasma]['angle'] += 8
    
    def draw_enemy(self, dt, event_list):
        global mute, powerups

        if self.enemy_rect.centery < 150 and powerups.pcollected != 'freeze':
            self.enemy_yspeed = 0.15
            self.enemy_xspeed = 0
        elif self.enemy_rect.centery >= 150 and powerups.pcollected != 'freeze':
            if self.set_enemy_speed:
                self.enemy_yspeed = 0
                self.enemy_xspeed = random.choice([0.5, -0.5])
                self.set_enemy_speed = False
                self.set_plasma()
                pg.time.set_timer(self.rotate_enemy_event, self.rotate_delay)

        if (self.enemy_health > 0 and
            self.weapon == 'laser' and
            self.enemy_angle == 0 and
            powerups.pcollected != 'freeze'):
            for event in event_list:
                if event.type == self.laser_event:
                    self.add_laser()
            self.draw_laser(dt)

        if (self.enemy_health > 0 and
            self.weapon == 'plasma' and
            self.enemy_angle == 0 and
            self.enemy_rect.centery >= 150 and
            powerups.pcollected != 'freeze'):
            self.draw_plasma(dt)

        if powerups.pcollected != 'freeze':
            if self.enemy_rect.left < 5:
                self.enemy_xspeed = 0.5
            elif self.enemy_rect.right > window_width-5:
                self.enemy_xspeed = -0.5

        if self.enemy_health > 0:
            self.cur_enemy_x += self.enemy_xspeed*dt
            self.cur_enemy_y += self.enemy_yspeed*dt
            #print(self.enemy_xspeed, end=' ' )

        self.enemy_rect.x = self.cur_enemy_x
        self.enemy_rect.y = self.cur_enemy_y

        for event in event_list:
            if event.type == self.rotate_enemy_event and powerups.pcollected != 'freeze':
                self.enemy_angle += 4
                self.lasers.clear()
                self.set_plasma()
                if self.weapon == 'plasma':
                    self.weapon = 'laser'
                else:
                    self.weapon = 'plasma'


        if self.enemy_health > 0:
            if not self.enemy_angle:
                window.blit(self.enemy_img,
                            (self.cur_enemy_x, self.cur_enemy_y))
            else:
                self.enemy_angle += 4

                self.rot_enemy  = pg.transform.rotate(self.enemy_img, self.enemy_angle)
                self.rot_enemy_rect = self.rot_enemy.get_rect(center=self.enemy_rect.center)

                self.flash_surface = self.rot_enemy

                window.blit(self.rot_enemy, self.rot_enemy_rect)
                
                if self.enemy_angle >= 180:
                    self.enemy_angle = 0
                    self.enemy_img = pg.transform.rotate(self.enemy_img, 180)
                    if self.weapon == 'plasma':
                        self.set_plasma()
                    
                    '''
                    if self.weapon == 'plasma':
                        self.set_plasma()
                        self.weapon = 'laser'
                        self.lasers.clear()
                    else:
                        self.lasers.clear()
                        self.weapon = 'plasma'
                        self.set_plasma()
                    '''
        else:
            for event in event_list:
                if event.type == self.enemy_flash:
                    self.flash_surface = self.rot_enemy if self.flash_surface == self.empty_img else self.empty_img
            window.blit(self.flash_surface,
                        (self.cur_enemy_x, self.cur_enemy_y))
        '''
        if (self.enemy_health > 0 and
            self.weapon == 'laser' and
            self.enemy_angle == 0):
            for event in event_list:
                if event.type == self.laser_event:
                    self.add_laser()
            self.draw_laser(dt)

        if (self.enemy_health > 0 and
            self.weapon == 'plasma' and
            self.enemy_angle == 0 and
            self.enemy_rect.centery >= 150):
            self.draw_plasma(dt)
        '''
            #for plasma in self.plasmas:
             #   if self.plasmas[plasma]['rect'].bottom >= window_width+10:
              #      self.set_plasma()
               #     break

        self.check_health(event_list)

    def check_health(self, event_list):
        global score_value, spawn_large_enemy_trigger1, spawn_medium_enemy_trigger1
        global spawn_large_enemy_trigger2, isinit_enemy_small_last, spawn_medium_enemy_trigger2
        global enemy_small_killed
        
        if self.enemy_health <= 0:
            self.lasers.clear()
            
            for event in event_list:
                if event.type == self.enemy_flash:
                    self.num_flash += 1
            if self.num_flash >= 12:
                score_value += 20
                spawn_large_enemy_trigger1 = False
                spawn_large_enemy_trigger2 = False
                spawn_medium_enemy_trigger1 = False
                spawn_medium_enemy_trigger2 = False
                isinit_enemy_small_last = False
                self.__init__()
                init_enemy_small_pos()
                increase_lvl()
                pg.time.set_timer(self.enemy_flash, 0)
                pg.time.set_timer(self.laser_event, 0)
                enemy_small_killed = 0

enemy_large = EnemyLarge()

spawn_large_enemy_trigger1 = False
spawn_large_enemy_trigger2 = False


#Flashing effect near the player battleship cannons
flash_img = pg.image.load('.\\resources\\images\\bullet\\laser32.png').convert_alpha()
blank_img = pg.image.load('.\\resources\\images\\bullet\\blank32.png').convert_alpha()
flash_img_size = flash_img_w, flash_img_h = flash_img.get_size()
flash_rect = flash_img.get_rect()
flash1X, flash1Y = player_rect.x-8, player_rect.y+2
flash2X, flash2Y = player_rect.x+player_img_w-24, player_rect.y+2
show_flash = True
num = 9

def draw_flash(prect, num):
    #global show_flash

    b1x, b1y = prect.x-8, prect.y+2
    b2x, b2y = prect.x+player_img_w-24, prect.y+2

    if 5 <= num < 10:
        #print('hi')
        window.blit(flash_img, (b1x, b1y))
        window.blit(flash_img, (b2x, b2y))
        if num == 9:
            return 0
        num += 1
    else:
        num += 1

    return num


#Player laser bullets properties and functions
laser_img = pg.image.load('.\\resources\\images\\bullet\\minus32.png').convert_alpha()
laser_img_size = laser_img_w, laser_img_h = laser_img.get_size()
laser_rect = laser_img.get_rect()
laser_xspeed = 0
laser_yspeed = 1.2
lasers = {}
i = 1 #Laser number
explosion_sound = mixer.Sound(r'.\resources\sounds\explosion1.wav')

def draw_laser(dt):
    global lasers, enemy_small, score_value, laser_img, enemy_medium
    global explosion_sound, hit_value, enemy_small_killed, channels

    delete = []
    for laser in lasers:
        if (lasers[laser]['laser1rect'].bottom <= -10 and
            lasers[laser]['laser2rect'].bottom <= -10):
            delete.append(laser)
            continue

        lasers[laser]['laserY_change'] = laser_yspeed*dt
        
        #Checking collision of lasers with different type of enemies 
        for enemy in enemy_small:
            if (is_collide(enemy_small[enemy]['rect'], lasers[laser]['laser1rect']) and
                enemy_small[enemy]['alive']):
                lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
                enemy_small[enemy]['alive'] = False
                score_value += 1
                hit_value += 1
                enemy_small_killed += 1
                if mute == False:
                    #explosion_sound = mixer.Sound(r'.\resources\sounds\explosion1.wav')
                    channels[1].play(explosion_sound)
            if (is_collide(enemy_small[enemy]['rect'], lasers[laser]['laser2rect']) and
                enemy_small[enemy]['alive']):
                lasers[laser]['laser2rect'].x = lasers[laser]['laser2rect'].y = -50
                enemy_small[enemy]['alive'] = False
                score_value += 1
                hit_value += 1
                enemy_small_killed += 1
                if mute == False:
                    #explosion_sound = mixer.Sound(r'.\resources\sounds\explosion2.wav')
                    channels[1].play(explosion_sound)

        if (is_collide_medium(enemy_medium.enemy_rect, lasers[laser]['laser1rect']) and
            enemy_medium.enemy_health > 0):
            lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
            enemy_medium.enemy_health -= 1
            hit_value += 1
            #print(enemy_medium.enemy_health)
            if mute == False:
                channels[1].play(explosion_sound)
        if (is_collide_medium(enemy_medium.enemy_rect, lasers[laser]['laser2rect']) and
            enemy_medium.enemy_health > 0):
            lasers[laser]['laser2rect'].x = lasers[laser]['laser2rect'].y = -50
            enemy_medium.enemy_health -= 1
            hit_value += 1
            #print(enemy_medium.enemy_health)
            if mute == False:
                channels[1].play(explosion_sound)

        if (is_collide_medium(enemy_large.enemy_rect, lasers[laser]['laser1rect']) and
            enemy_large.enemy_health > 0):
            lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
            enemy_large.enemy_health -= 1
            hit_value += 1
            #print(enemy_large.enemy_health)
            if mute == False:
                channels[1].play(explosion_sound)
        if (is_collide_medium(enemy_large.enemy_rect, lasers[laser]['laser2rect']) and
            enemy_large.enemy_health > 0):
            lasers[laser]['laser2rect'].x = lasers[laser]['laser2rect'].y = -50
            enemy_large.enemy_health -= 1
            hit_value += 1
            #print(enemy_large.enemy_health)
            if mute == False:
                channels[1].play(explosion_sound)
        
        lasers[laser]['cur_laser1_y'] -= lasers[laser]['laserY_change']
        lasers[laser]['cur_laser2_y'] -= lasers[laser]['laserY_change']
        lasers[laser]['laser1rect'].y = lasers[laser]['cur_laser1_y']
        lasers[laser]['laser2rect'].y = lasers[laser]['cur_laser2_y']
        L1x = lasers[laser]['laser1rect'].x
        L1y = lasers[laser]['cur_laser1_y']
        L2x = lasers[laser]['laser2rect'].x
        L2y = lasers[laser]['cur_laser2_y']

        window.blit(lasers[laser]['img'], (L1x, L1y))
        window.blit(lasers[laser]['img'], (L2x, L2y))

    for key in delete:
        del lasers[key]
    

def add_laser():
    global lasers, i, laser_img, player_rect, mute, channels

    if mute == False:
        laser_sound = mixer.Sound(r'.\resources\sounds\laser1.wav')
        channels[3].play(laser_sound)

    if i > 20:
        i = 0

    lasers['laser'+str(i)] = {}
    lasers['laser'+str(i)]['img'] = pg.image.load('.\\resources\\images\\bullet\\minus32.png')
    lasers['laser'+str(i)]['laserY_change'] = 0
    lasers['laser'+str(i)]['cur_laser1_y'] = player_rect.y-32
    lasers['laser'+str(i)]['cur_laser2_y'] = player_rect.y-32
    lasers['laser'+str(i)]['laser1rect'] = laser_img.get_rect()
    lasers['laser'+str(i)]['laser2rect'] = laser_img.get_rect()
    lasers['laser'+str(i)]['laser1rect'].x = player_rect.x-8
    lasers['laser'+str(i)]['laser1rect'].y = player_rect.y + 5
    lasers['laser'+str(i)]['laser2rect'].x = player_rect.x+player_img_w-24
    lasers['laser'+str(i)]['laser2rect'].y = player_rect.y + 5
    
    i += 1


def is_collide(enrect, lrect):
    if int(math.fabs(lrect.midtop[1] - enrect.center[1])) <= 55:
        if enrect.left <= lrect.midtop[0] <= enrect.right:
            return True

    return False

def is_collide_medium(enrect, lrect):
    if int(math.fabs(lrect.midtop[1] - enrect.center[1])) <= 80:
        if enrect.left <= lrect.midtop[0] <= enrect.right:
            return True

    return False

#Charge value properties and functions(for rocket)
charge_value = 0
charge_img_list = []
for i in range(1,13):
    charge_img_list.append(pg.image.load(fr'.\resources\images\power-up\charging-up\loader{i}(80).png').convert_alpha())
charge_rect = charge_img_list[0].get_rect(left=10, bottom=window_height-10)
rocket_img1 = pg.image.load(r'.\resources\images\power-up\charging-up\missile-fill56.png').convert_alpha()
rocket_rect = rocket_img1.get_rect(center=charge_rect.center)
hit_value = 0
charge_up_sound = mixer.Sound(r'.\resources\sounds\charge-up.wav')
charge_rot_img = charge_img_list[11]
charge_rot_angle = 1

def draw_charge_quantity():
    global charge_value, charge_img_list, charge_rect, rocket_img1, rocket_rect
    global hit_value, mute, charge_up_sound, charge_rot_img, charge_rot_angle, channels

    if charge_value > 0:
        if charge_value == 12:
            charge_rot_img = pg.transform.rotate(charge_img_list[11], charge_rot_angle)
            charge_rot_rect = charge_rot_img.get_rect(center=charge_rect.center)
            window.blit(charge_rot_img, charge_rot_rect)
            charge_rot_angle += 1
        else:    
            window.blit(charge_img_list[charge_value-1], charge_rect)

    window.blit(rocket_img1, rocket_rect)

    if hit_value >= 5:
        hit_value = 0
        if charge_value < 12:
            charge_value += 1
            if mute == False:
                channels[8].play(charge_up_sound)

    if charge_value == 0:
        charge_rot_angle = 1


#Player missile properties and functions
missile_img = pg.image.load(r'.\resources\images\bullet\missile-fill-small.png').convert_alpha()
missile_rect = missile_img.get_rect(midbottom=player_rect.midtop)
missile_yspeed = 0.7
missile_cur_x = missile_rect.x
missile_cur_y = missile_rect.y
missile_draw = False
missile_launch = False
missile_explosion_dict = {}
missile_explosion_delay = 200
missile_explosion_time_elapse = 0
explosion_i = 0
missile_explosion = False
explosion_center = (0, 0)
explosion_effect = True
missile_launch_sound = mixer.Sound(r'.\resources\sounds\rocket-deploy.wav')
missile_explosion_sound = mixer.Sound(r'.\resources\sounds\large-explosion-short.wav')
missile_explosion_sound.set_volume(0.7)

for i in range(1, 18):
    explosion = 'explosion' + str(i)
    missile_explosion_dict[explosion] = [pg.image.load(fr'.\resources\images\bullet\missile-explosion\{explosion}.png').convert_alpha()]

for explosion in missile_explosion_dict:
    missile_explosion_dict[explosion].append(missile_explosion_dict[explosion][0].get_rect())

explosion_list = list(missile_explosion_dict.keys())
explosion_cycle = explosion_list[explosion_i:explosion_i+3]

def draw_missile(dt):
    global missile_img, missile_rect, missile_yspeed, missile_cur_x
    global missile_cur_y, missile_draw, missile_explosion_time_elapse
    global explosion_i, explosion_cycle, player_rect, missile_explosion
    global explosion_center, enemy_small, score_value, enemy_medium
    global explosion_effect, enemy_large, window_rect, hit_value, channels
    global missile_explosion_sound, missile_launch_sound, enemy_small_killed

    if missile_draw:
        window.blit(missile_img, (missile_cur_x, missile_cur_y))

        missile_cur_y -= missile_yspeed * dt

        missile_rect.y = missile_cur_y

    if missile_rect.top <= 150:
        explosion_center = missile_rect.midtop
        missile_draw = False
        missile_rect.midbottom = player_rect.midtop
        missile_explosion = True

    #Checking collision of missile with different type of enemies
    for enemy in enemy_small:
        if (enemy_small[enemy]['rect'].colliderect(missile_rect) and
            enemy_small[enemy]['alive'] and
            missile_draw):
            explosion_center = missile_rect.midtop
            missile_draw = False
            missile_rect.midbottom = player_rect.midtop
            missile_explosion = True
            enemy_small[enemy]['alive'] = False
            score_value += 1
            hit_value += 1
            enemy_small_killed += 1

    if (enemy_medium.enemy_rect.colliderect(window_rect) and
        enemy_medium.enemy_rect.colliderect(missile_rect) and
        enemy_medium.enemy_health > 0 and
        explosion_effect and
        missile_draw):
        #lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
        enemy_medium.enemy_health = enemy_medium.enemy_health - 5 if enemy_medium.enemy_health > 5 else 0
        #print(enemy_medium.enemy_health)
        explosion_effect = False
        enemy_medium.lasers.clear()
        explosion_center = missile_rect.midtop
        missile_draw = False
        missile_rect.midbottom = player_rect.midtop
        missile_explosion = True
        hit_value += 2
        #if mute == False:
         #   explosion_sound.play()

    if (enemy_large.enemy_rect.colliderect(window_rect) and
        enemy_large.enemy_rect.colliderect(missile_rect) and
        enemy_large.enemy_health > 0 and
        explosion_effect and
        missile_draw):
        #lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
        enemy_large.enemy_health = enemy_large.enemy_health - 5 if enemy_large.enemy_health > 5 else 0
        #print(enemy_large.enemy_health)
        explosion_effect = False
        for plasma in enemy_large.plasmas:
            enemy_large.plasmas[plasma]['draw'] = False
        enemy_large.lasers.clear()
        explosion_center = missile_rect.midtop
        missile_draw = False
        missile_rect.midbottom = player_rect.midtop
        missile_explosion = True
        hit_value += 2
        #if mute == False:
         #   explosion_sound.play()
                

        
    if missile_explosion:
        if mute == False and missile_explosion_time_elapse == 0:
            channels[4].play(missile_explosion_sound)
        #print(explosion_cycle)
        for explosion in explosion_cycle:
            missile_explosion_dict[explosion][1].center = explosion_center
            window.blit(missile_explosion_dict[explosion][0],
                        missile_explosion_dict[explosion][1])

        missile_explosion_time_elapse += dt
        if missile_explosion_time_elapse >= 80:
            explosion_i += 1
            explosion_cycle = explosion_list[explosion_i:explosion_i+3]
            missile_explosion_time_elapse = 1

        if explosion_i == len(missile_explosion_dict)-1:
            missile_explosion_time_elapse = 0
            explosion_i = 0
            missile_explosion = False
            explosion_cycle = explosion_list[explosion_i:explosion_i+3]
            explosion_effect = True
            for explosion in missile_explosion_dict:
                missile_explosion_dict[explosion][1].center = (-1000, -1000)

        #Checking collision of explosion with different type of enemies 
        for enemy in enemy_small:
            if (enemy_small[enemy]['rect'].colliderect(missile_explosion_dict[explosion_cycle[-2]][1]) and
                enemy_small[enemy]['alive']):
                #lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
                enemy_small[enemy]['alive'] = False
                score_value += 1
                enemy_small_killed += 1

            if (enemy_small[enemy]['laser_rect'].colliderect(missile_explosion_dict[explosion_cycle[-2]][1]) and
                enemy_small[enemy]['laser_draw']):
                enemy_small[enemy]['laser_draw'] = False
                #if mute == False:
                    #explosion_sound = mixer.Sound(r'.\resources\sounds\explosion1.wav')
                    #explosion_sound.play()

        if (enemy_medium.enemy_rect.colliderect(window_rect) and
            enemy_medium.enemy_rect.colliderect(missile_explosion_dict[explosion_cycle[-2]][1]) and
            enemy_medium.enemy_health > 0 and
            explosion_effect):
            #lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
            enemy_medium.enemy_health = enemy_medium.enemy_health - 5 if enemy_medium.enemy_health > 5 else 0
            #print(enemy_medium.enemy_health)
            explosion_effect = False
            enemy_medium.lasers.clear()
            #if mute == False:
             #   explosion_sound.play()

        if (enemy_large.enemy_rect.colliderect(window_rect) and
            enemy_large.enemy_rect.colliderect(missile_explosion_dict[explosion_cycle[-2]][1]) and
            enemy_large.enemy_health > 0 and
            explosion_effect):
            #lasers[laser]['laser1rect'].x = lasers[laser]['laser1rect'].y = -50
            enemy_large.enemy_health = enemy_large.enemy_health - 5 if enemy_large.enemy_health > 5 else 0
            #print(enemy_large.enemy_health)
            explosion_effect = False
            for plasma in enemy_large.plasmas:
                enemy_large.plasmas[plasma]['draw'] = False
            enemy_large.lasers.clear()
            #if mute == False:
             #   explosion_sound.play()
    

#Player power-ups properties and functions
class PowerUps():

    def __init__(self):
        self.powerups = {
            'life' : {'img' : pg.image.load(r'.\resources\images\power-up\life-fill48.png').convert_alpha(),
                      'img_invert' : pg.image.load(r'.\resources\images\power-up\life-fill-invert48.png').convert_alpha(),
                      'rect' : pg.Rect(0, 0, 48, 48),
                      'sound' : mixer.Sound(r'.\resources\sounds\pickup-01.wav'),
                      'draw' : False,
                      'func' : self.life_powerup},
            'freeze' : {'img' : pg.image.load(r'.\resources\images\power-up\freeze-fill48.png').convert_alpha(),
                        'img_invert' : pg.image.load(r'.\resources\images\power-up\freeze-fill-invert48.png').convert_alpha(),
                        'rect' : pg.Rect(0, 0, 48, 48),
                        'sound' : mixer.Sound(r'.\resources\sounds\freeze-loud.wav'),
                        'sound2' : mixer.Sound(r'.\resources\sounds\depressurized.wav'),
                        'draw' : False,
                        'func' : self.freeze_powerup},
            'charge' : {'img' : pg.image.load(r'.\resources\images\power-up\charge-fill48.png').convert_alpha(),
                        'img_invert' : pg.image.load(r'.\resources\images\power-up\charge-fill-invert48.png').convert_alpha(),
                        'rect' : pg.Rect(0, 0, 48, 48),
                        'sound' : mixer.Sound(r'.\resources\sounds\charge-up.wav'),
                        'draw' : False,
                        'func' : self.charge_powerup},
            }

        self.yspeed = 0.2
        self.pchoice = None
        self.time_elapse = 0
        self.pcollected = None
        
        self.original_speed = {
            'enemy_small' : [],
            'enemy_medium' : [],
            'enemy_large' : []
            }
        self.freeze_time = 0
        

    def draw(self, dt):

        if self.pchoice is None:
            option_list = list(self.powerups.keys()) + [None] 
            self.pchoice = random.choices(option_list, [1, 1, 2, 2996])[0]
            if self.pchoice is not None:
                self.powerups[self.pchoice]['rect'].center = (random.randint(50, window_width-50), -100)
                self.powerups[self.pchoice]['draw'] = True
                self.time_elapse = 0

        if self.pchoice is not None:
            
            if self.powerups[self.pchoice]['draw']:
                if self.time_elapse <= 700:
                    window.blit(self.powerups[self.pchoice]['img'], self.powerups[self.pchoice]['rect'])
                elif self.time_elapse <= 1400:
                    window.blit(self.powerups[self.pchoice]['img_invert'], self.powerups[self.pchoice]['rect'])

            if self.time_elapse > 1400:
                    self.time_elapse = 0

            self.time_elapse += dt
                    
            self.powerups[self.pchoice]['rect'].y += self.yspeed * dt

            if self.powerups[self.pchoice]['rect'].y > window_height+5:
                self.powerups[self.pchoice]['rect'].center = (0,0)
                self.powerups[self.pchoice]['draw'] = False
                self.pchoice = None
                self.pcollected = None

    def life_powerup(self, dt):
        global player_health, mute, player_max_health, channels

        self.pcollected = 'life'

        if player_health < player_max_health and self.powerups['life']['draw']:
            player_health += 1
            if mute == False:
                channels[5].play(self.powerups['life']['sound'])

            self.powerups['life']['draw'] = False
            self.pchoice = None
            self.pcollected = None

    def charge_powerup(self, dt):
        global charge_value, mute, channels

        self.pcollected = 'charge'

        if charge_value < 12 and self.powerups['charge']['draw']:
            charge_value += 1
            if mute == False:
                channels[8].play(self.powerups['charge']['sound'])

            self.powerups['charge']['draw'] = False
            self.pchoice = None
            self.pcollected = None

    def freeze_powerup(self, dt):
        global enemy_small, mute, player_rect, enemy_medium, enemy_large, channels

        self.pcollected = 'freeze'

        if self.powerups['freeze']['draw']:           
            #if mute == False:
             #   self.powerups['charge']['sound'].play()
            self.powerups['freeze']['draw'] = False
            #self.pchoice = None

        self.powerups['freeze']['rect'].center = player_rect.center 

        if self.freeze_time == 0:
            if mute == False:
                channels[6].play(self.powerups['freeze']['sound'])
            for enemy in enemy_small:
                self.original_speed['enemy_small'].append([enemy_small[enemy]['enemy_smallX_change'],
                                                           enemy_small[enemy]['enemy_smallY_change']])
                enemy_small[enemy]['enemy_smallX_change'] = 0
                enemy_small[enemy]['enemy_smallY_change'] = 0

            self.original_speed['enemy_medium'].append([enemy_medium.enemy_xspeed,
                                                        enemy_medium.enemy_yspeed])
            enemy_medium.enemy_xspeed = 0
            enemy_medium.enemy_yspeed = 0
            enemy_medium.lasers.clear()

            self.original_speed['enemy_large'].append([enemy_large.enemy_xspeed,
                                                       enemy_large.enemy_yspeed])
            enemy_large.plasma_sound.fadeout(20)
            enemy_large.enemy_xspeed = 0
            enemy_large.enemy_yspeed = 0
            enemy_large.lasers.clear()
            enemy_large.set_plasma()
                

        self.freeze_time += dt
        if 2700 >= self.freeze_time >= 2650:
            if mute == False:
                channels[7].play(self.powerups['freeze']['sound2'])
        if self.freeze_time >= 3000:
            for enemy, orig_speed in zip(enemy_small, self.original_speed['enemy_small']):
                enemy_small[enemy]['enemy_smallX_change'] = orig_speed[0]
                enemy_small[enemy]['enemy_smallY_change'] = orig_speed[1]

            enemy_medium.enemy_xspeed = self.original_speed['enemy_medium'][0][0]
            enemy_medium.enemy_yspeed = self.original_speed['enemy_medium'][0][1]
            
            enemy_large.enemy_xspeed = self.original_speed['enemy_large'][0][0]
            enemy_large.enemy_yspeed = self.original_speed['enemy_large'][0][1]
            
            self.original_speed['enemy_small'].clear()
            self.original_speed['enemy_medium'].clear()
            self.original_speed['enemy_large'].clear()

            self.powerups['freeze']['rect'].center = (0,0)
            self.freeze_time = 0
            self.pchoice = None
            self.pcollected = None
        

powerups = PowerUps()

#Moving background properties and functions
class Background():
    def __init__(self):
        self.b_r1c1 = pg.image.load(r'.\resources\images\background\background_horizontal1.png').convert_alpha()
        self.b_r1c2 = pg.image.load(r'.\resources\images\background\background_horizontal2.png').convert_alpha()
        self.b_r2c1 = pg.image.load(r'.\resources\images\background\background_vertical1.png').convert_alpha()
        self.b_r2c2 = pg.image.load(r'.\resources\images\background\background_vertical2.png').convert_alpha()
        self.translucent = pg.image.load(r'.\resources\images\background\background(40%alpha).png').convert_alpha()

        self.xspeed = 0
        self.yspeed = 0.15

        self.b_r1c1_rect = self.b_r1c1.get_rect(center=(window_width/2, window_height/2))
        self.b_r1c2_rect = self.b_r1c2.get_rect(midleft=self.b_r1c1_rect.midright)
        self.b_r2c1_rect = self.b_r2c1.get_rect(midtop=self.b_r1c1_rect.midbottom)
        self.b_r2c2_rect = self.b_r2c2.get_rect(midleft=self.b_r2c1_rect.midright)

        self.row_rects = [[self.b_r1c1_rect, self.b_r1c2_rect],
                      [self.b_r2c1_rect, self.b_r2c2_rect]]
        self.col_rects = [list(col) for col in zip(*self.row_rects)]
        
    def draw_background(self, dt):
        global playerX_change, playerY_change, window_rect
        
        if playerX_change == 0:
            self.xspeed = 0
        elif playerX_change > 0:
            self.xspeed = -0.2
        elif playerX_change < 0:
            self.xspeed = 0.2
        if playerY_change == 0:
            self.yspeed = 0.15
        elif playerY_change > 0:
            self.yspeed = 0.1
        elif playerY_change < 0:
            self.yspeed = 0.25

                
        self.b_r1c1_rect.centerx += self.xspeed*dt
        self.b_r1c1_rect.centery += self.yspeed*dt
        self.b_r1c2_rect.centerx += self.xspeed*dt
        self.b_r1c2_rect.centery += self.yspeed*dt
        self.b_r2c1_rect.centerx += self.xspeed*dt
        self.b_r2c1_rect.centery += self.yspeed*dt
        self.b_r2c2_rect.centerx += self.xspeed*dt
        self.b_r2c2_rect.centery += self.yspeed*dt

        #win_rect = window.get_rect(topleft=(0,0))

        if self.b_r1c1_rect.colliderect(window_rect):
            window.blit(self.b_r1c1, self.b_r1c1_rect)
            #print('1', end='')
        if self.b_r1c2_rect.colliderect(window_rect):
            window.blit(self.b_r1c2, self.b_r1c2_rect)
            #print('2', end='')
        if self.b_r2c1_rect.colliderect(window_rect):
            window.blit(self.b_r2c1, self.b_r2c1_rect)
            #print('3', end='')
        if self.b_r2c2_rect.colliderect(window_rect):
            window.blit(self.b_r2c2, self.b_r2c2_rect)
            #print('4', end='')
            
        '''
        window.blit(self.b_r1c1, self.b_r1c1_rect)
        window.blit(self.b_r1c2, self.b_r1c2_rect)
        window.blit(self.b_r2c1, self.b_r2c1_rect)
        window.blit(self.b_r2c2, self.b_r2c2_rect)
        '''
        window.blit(self.translucent, (0,0))

        
        for row in self.row_rects:
            for i, rect in enumerate(row):
                if rect.left >= -20:
                    if i == 0:
                        row[1].midright = rect.midleft
                    elif i == 1:
                        row[0].midright = rect.midleft

                if rect.right <= window_width+20:
                    if i == 0:
                        row[1].midleft = rect.midright
                    elif i == 1:
                        row[0].midleft = rect.midright

        for col in self.col_rects:
            for i, rect in enumerate(col):
                if rect.top >= -20:
                    if i == 0:
                        col[1].midbottom = rect.midtop
                    elif i == 1:
                        col[0].midbottom = rect.midtop
        
background = Background()       


#Backgound Objects properties and functions 
class BackgroundObjects():
    
    def __init__(self):
        
        self.objects = {}

        i = 1        
        for obj in os.listdir(r'.\resources\images\background-objects'):
            if obj.endswith(r'.png'):
                path = '.\\resources\\images\\background-objects\\' + obj         
                self.objects['object'+str(i)] = {}
                self.objects['object'+str(i)]['img'] = pg.image.load(path).convert_alpha()
                i += 1

        self.xspeed = 0
        self.yspeed = [0.1, 0.2, 0.3] #[0.06, 0.12, 0.18]

        self.obj_draw = []
        
        self.set_param()
        
    def set_param(self):

        for obj in self.objects:
            self.objects[obj]['rect'] = self.objects[obj]['img'].get_rect()
            self.objects[obj]['xchange'] = self.xspeed
            
            if self.objects[obj]['img'].get_width() == 32:
                self.objects[obj]['ychange'] = self.yspeed[0]
            elif self.objects[obj]['img'].get_width() == 40:
                self.objects[obj]['ychange'] = self.yspeed[1]
            elif self.objects[obj]['img'].get_width() == 48:
                self.objects[obj]['ychange'] = self.yspeed[2]
                
            self.objects[obj]['cur_x'] = random.randint(20, window_width-self.objects[obj]['img'].get_width()-20)
            self.objects[obj]['cur_y'] = random.randint(-1000, -50)

    def _reset(self, obj):
        self.objects[obj]['cur_x'] = random.randint(20, window_width-self.objects[obj]['img'].get_width()-20)
        self.objects[obj]['cur_y'] = random.randint(-1000, -50)

    def draw_objects(self, dt):
        obj = random.choice(list(self.objects.keys()))

        del_list = []

        if len(self.obj_draw) < 3 and obj not in self.obj_draw:
            self._reset(obj)
            self.obj_draw.append(obj)

        for obj in self.obj_draw:
            self.objects[obj]['cur_x'] += self.objects[obj]['xchange']*dt
            self.objects[obj]['cur_y'] += self.objects[obj]['ychange']*dt

            self.objects[obj]['rect'].topleft = (self.objects[obj]['cur_x'],
                                                 self.objects[obj]['cur_y'])

            window.blit(self.objects[obj]['img'],
                        (self.objects[obj]['cur_x'], self.objects[obj]['cur_y']))

            if self.objects[obj]['rect'].top > window_height + 10:
                del_list.append(obj)

        for obj in del_list:
            self.obj_draw.remove(obj)

background_objects = BackgroundObjects()        


#Score properties and functions
score_value = 0
score_font = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 30)
score_background = {
    '126' : pg.image.load(r'.\resources\images\text-background\score-background126.png').convert_alpha(),
    '143' : pg.image.load(r'.\resources\images\text-background\score-background143.png').convert_alpha(),
    '160' : pg.image.load(r'.\resources\images\text-background\score-background160.png').convert_alpha(),
    '187' : pg.image.load(r'.\resources\images\text-background\score-background187.png').convert_alpha()
    }
scoreX = 14
scoreY = 10
#print(score_font.size('Score : ' + str(score_value)))
def draw_score(x, y):
    if score_value <= 9:
        window.blit(score_background['126'], (x-4, y+1))
    elif 9 < score_value <= 99:
        window.blit(score_background['143'], (x-4, y+1))
    elif score_value > 99:
        window.blit(score_background['160'], (x-4, y+1))
    elif score_value > 999:
        window.blit(score_background['187'], (x-4, y+1))
        
    score = score_font.render('Score : ' + str(score_value), True, (0,0,0))
    window.blit(score, (x,y))
    return

#Level properties and functions
lvl_value = 1
lvl_font = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 30)
lvl_background = {
    '126' : pg.image.load(r'.\resources\images\text-background\score-background126.png').convert_alpha(),
    '143' : pg.image.load(r'.\resources\images\text-background\score-background143.png').convert_alpha(),
    }
lvlX = 14
lvlY = 42+10+10
#print(score_font.size('Score : ' + str(score_value)))
def draw_lvl():
    global lvl_value, lvl_font, lvl_background, lvlX, lvlY
    
    if lvl_value <= 9:
        window.blit(lvl_background['126'], (lvlX-4, lvlY+1))
    elif lvl_value > 9:
        window.blit(lvl_background['143'], (lvlX-4, lvlY+1))
        
    lvl = lvl_font.render('Level : ' + str(lvl_value), True, (0,0,0))
    window.blit(lvl, (lvlX,lvlY))
    return

life_increase_sound = mixer.Sound(r'.\resources\sounds\pickup-01.wav')
def increase_lvl():
    global lvl_value, enemy_small_xspeed, enemy_small_yspeed, player_health, player_max_health
    global life_increase_sound, charge_value, charge_up_sound, mute, channels

    lvl_value += 1

    if charge_value < 12:
        charge_value += 1
        if mute == False:
            channels[8].play(charge_up_sound)

    if player_health < player_max_health:
        player_health += 1
        if mute == False:
            channels[5].play(life_increase_sound)

    if lvl_value and lvl_value%5 == 0:
        enemy_small_xspeed += 0.025 #0.5
        enemy_small_yspeed += 0.005 #0.1

    
#Only Image Buttons properties and functions
class OnlyImgButton():
    def __init__(self, img_inactive, img_active, x, y):
        self.img_inactive = img_inactive
        self.img_active = img_active
        self.btn_inactiveX = x
        self.btn_inactiveY = y
        self.btn_activeX = None
        self.btn_activeY = None
        self.rect_inactive = None
        self.rect_active = None
        self.state = 'inactive'
        self.set_param()

    def set_param(self):
        self.rect_inactive = self.img_inactive.get_rect(x=self.btn_inactiveX, y=self.btn_inactiveY)
        self.rect_active = self.img_active.get_rect()
        self.rect_active.center = self.rect_inactive.center
        self.rect_active.height = self.img_active.get_height()
        self.rect_active.width = self.img_active.get_width()
        self.btn_activeX = self.rect_active.x
        self.btn_activeY = self.rect_active.y

    def update_param(self):
        self.btn_inactiveX = window_width-pause_btn_inactive_img.get_width()-15
        self.set_param()

    def update_param2(self, x, y):
        self.btn_inactiveX = x
        self.btn_inactiveY = y
        self.set_param()

    def draw_button(self, command=None, event_list=None, screenshot=None):
        mouse_pos = pg.mouse.get_pos()
        #pg.event.clear()
        mouse_click = pg.mouse.get_pressed()

        if self.state == 'inactive':
            window.blit(self.img_inactive, (self.btn_inactiveX, self.btn_inactiveY))
            
            r = self.img_inactive.get_size()[0]/2

            d = math.sqrt((mouse_pos[0]-self.rect_inactive.center[0])**2 + \
                          (mouse_pos[1]-self.rect_inactive.center[1])**2)

            if d <= r:
                self.state = 'active'

        elif self.state == 'active':
            #window.blit(self.img_active, (self.btn_activeX, self.btn_activeY))
            
            r = self.img_active.get_size()[0]/2

            d = math.sqrt((mouse_pos[0]-self.rect_active.center[0])**2 + \
                          (mouse_pos[1]-self.rect_active.center[1])**2)

            if d <= r:
                if event_list:
                    for event in event_list:
                        if event.type == pg.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                if screenshot:
                                    command(screenshot)
                                else:
                                    command()
            else:
                self.state = 'inactive'

            window.blit(self.img_active, (self.btn_activeX, self.btn_activeY))

pause_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\pause40.png').convert_alpha()
pause_btn_active_img = pg.image.load(r'.\resources\images\buttons\pause56.png').convert_alpha()
pause_btn_inactive_x = window_width-pause_btn_inactive_img.get_width()-15
pause_btn_inactive_y = 20

pause_btn = OnlyImgButton(pause_btn_inactive_img, pause_btn_active_img,
                          pause_btn_inactive_x, pause_btn_inactive_y)

play_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\play40.png').convert_alpha()
play_btn_active_img = pg.image.load(r'.\resources\images\buttons\play56.png').convert_alpha()
play_btn_inactive_x = window_width-play_btn_inactive_img.get_width()-15
play_btn_inactive_y = 20

play_btn = OnlyImgButton(play_btn_inactive_img, play_btn_active_img,
                          play_btn_inactive_x, play_btn_inactive_y)
play_btn.state = 'active'

paused = True
def play_command():
    global paused
    
    paused = False

    mixer.music.set_volume(0.7)
    


pause_txt_background = pg.image.load(r'.\resources\images\text-background\pause-background1920.png').convert_alpha()
def pause_command(screenshot):
    global paused, window_width, window_height, pause_txt_background
    
    paused = True

    #screenshot = pg.Surface((window_width, window_height))
    #screenshot.blit(window, (0,0))
    #pg.image.save(screenshot, r".\resources\images\screenshots\screenshot.png")
    
    textFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Bold.ttf', 100)
    textSurface = textFont.render('Paused', True, (0,0,0))
    textRect = textSurface.get_rect()
    textRect.center = ((window_width/2),(window_height/2))

    textBackgroundRect = pause_txt_background.get_rect()
    textBackgroundRect.center = textRect.center

    mixer.music.set_volume(0.3)

    #window_background = pg.image.load(r".\resources\images\screenshots\screenshot.png")  

    while paused:

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()
                
                play_btn.update_param()
                mute_btn.update_param()
                unmute_btn.update_param()
                '''
                
                textRect.center = ((window_width/2),(window_height/2))
                textBackgroundRect.center = textRect.center

        window.blit(pg.transform.scale(screenshot, (window_width, window_height)), (0,0))#pg.transform.scale(screenshot, (window_width, window_height))

        window.blit(pause_txt_background, textBackgroundRect)
        window.blit(textSurface, textRect)

        play_btn.update_param()
        play_btn.draw_button(play_command, event_list)

        if mute:
            unmute_btn.draw_button(unmute_command, event_list)
        else:
            mute_btn.draw_button(mute_command, event_list)

        pg.display.update()


mute_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\mute40.png').convert_alpha()
mute_btn_active_img = pg.image.load(r'.\resources\images\buttons\mute56.png').convert_alpha()
mute_btn_inactive_x = window_width - mute_btn_inactive_img.get_width() - 15
mute_btn_inactive_y = 20 + mute_btn_inactive_img.get_height() + 20

mute_btn = OnlyImgButton(mute_btn_inactive_img, mute_btn_active_img,
                          mute_btn_inactive_x, mute_btn_inactive_y)

unmute_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\unmute40.png').convert_alpha()
unmute_btn_active_img = pg.image.load(r'.\resources\images\buttons\unmute56.png').convert_alpha()
unmute_btn_inactive_x = window_width - unmute_btn_inactive_img.get_width() - 15
unmute_btn_inactive_y = 20 + unmute_btn_inactive_img.get_height() + 20

unmute_btn = OnlyImgButton(unmute_btn_inactive_img, unmute_btn_active_img,
                           unmute_btn_inactive_x, unmute_btn_inactive_y)
unmute_btn.state = 'active'

mute = False  
def mute_command():
    global mute
    
    mixer.music.pause()
    mute = True

def unmute_command():
    global mute
    
    mixer.music.play(-1)
    mute = False

home_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\home40.png').convert_alpha()
home_btn_active_img = pg.image.load(r'.\resources\images\buttons\home56.png').convert_alpha()
home_btn_inactive_x = window_width - home_btn_inactive_img.get_width() - 15
home_btn_inactive_y = 20 + 2*home_btn_inactive_img.get_height() + 20 +20

home_btn = OnlyImgButton(home_btn_inactive_img, home_btn_active_img,
                           home_btn_inactive_x, home_btn_inactive_y)

wait_exit = False
def home_command(screenshot):
    global wait_exit, window_width, window_height
    
    wait_exit = True
    mixer.music.set_volume(0.3)

    #screenshot = pg.Surface((window_width, window_height))
    #screenshot.blit(window, (0,0))
    #pg.image.save(screenshot, r".\resources\images\screenshots\screenshot.png")
    
    textFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 80)
    textSurface = textFont.render('Exit to Main Menu?', True, (0,0,0))
    textRect = textSurface.get_rect()
    textRect.center = ((window_width/2),(window_height/2)-60)

    home_txt_background = pg.image.load(r'.\resources\images\text-background\home-background1920.png').convert_alpha()
    textBackgroundRect = home_txt_background.get_rect()
    textBackgroundRect.center = window.get_rect().center

    yes_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\yes72.png').convert_alpha()
    yes_btn_active_img = pg.image.load(r'.\resources\images\buttons\yes88.png').convert_alpha()
    yes_btn_rect = yes_btn_inactive_img.get_rect()
    yes_btn_rect.center = ((window_width*3/8),(window_height/2)+60)

    yes_btn = OnlyImgButton(yes_btn_inactive_img, yes_btn_active_img,
                           yes_btn_rect.x, yes_btn_rect.y)

    no_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\no72.png').convert_alpha()
    no_btn_active_img = pg.image.load(r'.\resources\images\buttons\no88.png').convert_alpha()
    no_btn_rect = no_btn_inactive_img.get_rect()
    no_btn_rect.center = ((window_width*5/8),(window_height/2)+60)

    no_btn = OnlyImgButton(no_btn_inactive_img, no_btn_active_img,
                           no_btn_rect.x, no_btn_rect.y)

    #window_background = pg.image.load(r".\resources\images\screenshots\screenshot.png")  

    while wait_exit:

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()
                '''
                
                yes_btn_rect.center = ((window_width*3/8),(window_height/2)+60)
                no_btn_rect.center = ((window_width*5/8),(window_height/2)+60)
                yes_btn.update_param2(yes_btn_rect.x, yes_btn_rect.y)
                no_btn.update_param2(no_btn_rect.x, no_btn_rect.y)

        window.blit(pg.transform.scale(screenshot, (window_width, window_height)), (0,0))

        textBackgroundRect.center = window.get_rect().center
        textRect.center = ((window_width/2),(window_height/2)-60)
        window.blit(home_txt_background, textBackgroundRect)
        window.blit(textSurface, textRect)

        yes_btn.draw_button(yes_command, event_list)
        no_btn.draw_button(no_command, event_list)

        #play_btn.draw_button(play_command, event_list)

        #if mute:
         #   unmute_btn.draw_button(unmute_command, event_list)
        #else:

         #   mute_btn.draw_button(mute_command, event_list)

        pg.display.update()

def no_command():
    global wait_exit

    wait_exit = False

def yes_command():
    global wait_exit, intro, reset_game, score_value

    wait_exit = False
    intro = True
    reset()
    #reset_game = True

    #if score_value > 0:
     #   update_highscore()
    #score_value = 0


#Text Buttons with image properties and functions 
class TxtButton(OnlyImgButton):

    def __init__(self, img_inactive, img_active, imgx, imgy, bg_inactive, bg_active, bgcx, bgcy, text):
        self.text = text
        self.bg_inactive = bg_inactive.convert_alpha()
        self.bg_active = bg_active.convert_alpha()
        self.bg_centerX = bgcx
        self.bg_centerY = bgcy
        self.bg_rect_inactive = None
        self.bg_rect_active = None
        self.textFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 40)
        self.textSurface = None
        self.textRect = None
        self.mask_inactive = None
        self.mask_active = None
        super().__init__(img_inactive, img_active, imgx, imgy)

    def set_param(self):
        self.rect_inactive = self.img_inactive.get_rect(x=self.btn_inactiveX, y=self.btn_inactiveY)
        self.rect_active = self.img_active.get_rect()
        self.rect_active.center = self.rect_inactive.center
        self.rect_active.height = self.img_active.get_height()
        self.rect_active.width = self.img_active.get_width()
        self.btn_activeX = self.rect_active.x
        self.btn_activeY = self.rect_active.y
        self.bg_rect_inactive = self.bg_inactive.get_rect(center=(self.bg_centerX, self.bg_centerY))
        self.bg_rect_active = self.bg_active.get_rect(center=(self.bg_centerX, self.bg_centerY))
        self.rect_inactive.center = (self.bg_rect_inactive.center[0]-160, self.bg_rect_inactive.center[1])
        self.rect_active.center = (self.bg_rect_active.center[0]-160, self.bg_rect_active.center[1])
        self.textSurface_inactive = self.textFont.render(self.text, True, (0,0,0))
        self.textSurface_active = self.textFont.render(self.text, True, (255,255,255))
        self.textRect = self.textSurface_inactive.get_rect(center=(self.bg_rect_inactive.centerx, self.bg_rect_inactive.centery-4))
        self.mask_inactive = pg.mask.from_surface(self.bg_inactive, 0)
        self.mask_active = pg.mask.from_surface(self.bg_active)

    def update_param(self):
        self.bg_centerX = window_width/2 
        self.set_param()

    def draw_button(self, command=None, event_list=None):
        mouse_pos = pg.mouse.get_pos()
        #pg.event.clear()
        mouse_click = pg.mouse.get_pressed()

        if self.state == 'inactive':
            window.blit(self.bg_inactive, self.bg_rect_inactive)
            window.blit(self.img_inactive, self.rect_inactive)
            window.blit(self.textSurface_inactive, self.textRect)

            try:
                if self.mask_inactive.get_at((mouse_pos[0]-self.bg_rect_inactive.x,
                                              mouse_pos[1]-self.bg_rect_inactive.y)):
                    self.state = 'active'
            except IndexError:
                pass

        elif self.state == 'active':
            window.blit(self.bg_active, self.bg_rect_active)
            window.blit(self.img_active, self.rect_active)
            window.blit(self.textSurface_active, self.textRect)
            
            try:
                if self.bg_rect_active.collidepoint(mouse_pos):
                    if self.mask_active.get_at((mouse_pos[0]-self.bg_rect_active.x,
                                                mouse_pos[1]-self.bg_rect_active.y)):
                        if event_list:
                            for event in event_list:
                                if event.type == pg.MOUSEBUTTONDOWN:
                                    if event.button == 1:
                                        self.state = 'inactive'
                                        command()
                                
                    else:
                        self.state = 'inactive'
                else:
                    self.state = 'inactive'
            except IndexError:
                pass


play_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\main menu\play(b)72.png').convert_alpha()
play_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\main menu\play(w)72.png').convert_alpha()
background_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background400,64.png').convert_alpha()
background_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background-fill400,64.png').convert_alpha()
background_text_btn_active_rect = background_text_btn_active_img.get_rect()
background_text_btn_active_rect.center = (window_width/2, window_height/2-15)
play_text_btn_inactive_rect = play_text_btn_inactive_img.get_rect()
play_text_btn_inactive_rect.center = (background_text_btn_active_rect.center[0]-160, background_text_btn_active_rect.center[1])

play_text_btn = TxtButton(play_text_btn_inactive_img, play_text_btn_active_img,
                          play_text_btn_inactive_rect.x, play_text_btn_inactive_rect.y,
                          background_text_btn_inactive_img, background_text_btn_active_img,
                          background_text_btn_active_rect.center[0], background_text_btn_active_rect.center[1],
                          'Play')

def play_text_command():
    global intro
    intro = False

how_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\main menu\how(b)64.png').convert_alpha()
how_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\main menu\how(w)64.png').convert_alpha()
background_text_btn_active_rect5 = background_text_btn_active_img.get_rect()
background_text_btn_active_rect5.center = (window_width/2, window_height/2-15+80)
how_text_btn_inactive_rect = how_text_btn_inactive_img.get_rect()
how_text_btn_inactive_rect.center = (background_text_btn_active_rect5.center[0]-160, background_text_btn_active_rect5.center[1])

how_text_btn = TxtButton(how_text_btn_inactive_img, how_text_btn_active_img,
                         how_text_btn_inactive_rect.x, how_text_btn_inactive_rect.y,
                         background_text_btn_inactive_img, background_text_btn_active_img,
                         background_text_btn_active_rect5.center[0], background_text_btn_active_rect5.center[1],
                         'How to Play')

highscore_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\main menu\list(b)64.png').convert_alpha()
highscore_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\main menu\list(w)64.png').convert_alpha()
#background_text_btn_inactive_img2 = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background400,72.png').convert_alpha()
#background_text_btn_active_img2 = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background-fill400,72.png').convert_alpha()
background_text_btn_active_rect2 = background_text_btn_active_img.get_rect()
background_text_btn_active_rect2.center = (window_width/2, window_height/2-15+80+80)
highscore_text_btn_inactive_rect = highscore_text_btn_inactive_img.get_rect()
highscore_text_btn_inactive_rect.center = (background_text_btn_active_rect2.center[0]-160, background_text_btn_active_rect2.center[1])

highscore_text_btn = TxtButton(highscore_text_btn_inactive_img, highscore_text_btn_active_img,
                               highscore_text_btn_inactive_rect.x, highscore_text_btn_inactive_rect.y,
                               background_text_btn_inactive_img, background_text_btn_active_img,
                               background_text_btn_active_rect2.center[0], background_text_btn_active_rect2.center[1],
                               'Highscores')

credit_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\main menu\credit(b)64.png').convert_alpha()
credit_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\main menu\credit(w)64.png').convert_alpha()
background_text_btn_active_rect4 = background_text_btn_active_img.get_rect()
background_text_btn_active_rect4.center = (window_width/2, window_height/2-15+80+80+80)
credit_text_btn_inactive_rect = credit_text_btn_inactive_img.get_rect()
credit_text_btn_inactive_rect.center = (background_text_btn_active_rect4.center[0]-160, background_text_btn_active_rect4.center[1])

credit_text_btn = TxtButton(credit_text_btn_inactive_img, credit_text_btn_active_img,
                          credit_text_btn_inactive_rect.x, credit_text_btn_inactive_rect.y,
                          background_text_btn_inactive_img, background_text_btn_active_img,
                          background_text_btn_active_rect4.center[0], background_text_btn_active_rect4.center[1],
                          'Credits')

quit_text_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\main menu\quit(b)64.png').convert_alpha()
quit_text_btn_active_img = pg.image.load(r'.\resources\images\buttons\main menu\quit(w)64.png').convert_alpha()
#background_text_btn_inactive_img3 = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background400,72.png')
#background_text_btn_active_img3 = pg.image.load(r'.\resources\images\buttons\text-button-background\text-button background-fill400,72.png')
background_text_btn_active_rect3 = background_text_btn_active_img.get_rect()
background_text_btn_active_rect3.center = (window_width/2, window_height/2-15+80+80+80+80)
quit_text_btn_inactive_rect = quit_text_btn_inactive_img.get_rect()
quit_text_btn_inactive_rect.center = (background_text_btn_active_rect3.center[0]-160, background_text_btn_active_rect3.center[1])

quit_text_btn = TxtButton(quit_text_btn_inactive_img, quit_text_btn_active_img,
                          quit_text_btn_inactive_rect.x, quit_text_btn_inactive_rect.y,
                          background_text_btn_inactive_img, background_text_btn_active_img,
                          background_text_btn_active_rect3.center[0], background_text_btn_active_rect3.center[1],
                          'Quit')

def quit_text_command():
    if score_value:
        update_highscore()
    pg.quit()
    sys.exit(0)


#Main Menu
intro = True
def game_intro():
    global intro, window_width, window_height, mute_btn, unmute_btn, mute
    global window_rect

    textFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 100)
    textSurface1 = textFont.render('Space', True, (0,0,0))
    textSurface2 = textFont.render('Overkill', True, (0,0,0))
    textRect1 = textSurface1.get_rect()
    textRect2 = textSurface2.get_rect()
    textRect1.center = ((window_width/2), (window_height/8))#(window_height/12)
    textRect2.center = ((window_width/2), (window_height/8)+120)

    developerFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 25)
    developerSurface1 = developerFont.render('Developed by : ', True, (0,0,0))
    developerSurface2 = developerFont.render('Luv Gautam', True, (0,0,0))
    developerRect1 = developerSurface1.get_rect()
    developerRect2 = developerSurface2.get_rect()
    developerRect1.bottomright = (window_width-5, window_height-5-35)
    developerRect2.midbottom = (developerRect1.centerx, window_height-5)

    mute_btn.btn_inactiveX = window_width - mute_btn_inactive_img.get_width() - 15
    mute_btn.btn_inactiveY = 20
    mute_btn.update_param()
    unmute_btn.btn_inactiveX = window_width - unmute_btn_inactive_img.get_width() - 15
    unmute_btn.btn_inactiveY = 20
    unmute_btn.update_param()

    game_intro_img1 = pg.image.load(r'.\resources\images\player\battleship(90)192.png').convert_alpha()
    game_intro_img2 = pg.image.load(r'.\resources\images\enemy\enemy-medium(90)192.png').convert_alpha()
    game_intro_rect1 = game_intro_img1.get_rect(midleft=(window_width/8, textRect1.bottom))
    game_intro_rect2 = game_intro_img2.get_rect(midleft=(window_width*6/8, textRect1.bottom))

    play_text_btn.update_param()
    highscore_text_btn.update_param()
    quit_text_btn.update_param()
    credit_text_btn.update_param()
    how_text_btn.update_param()

    intro_clock = pg.time.Clock()
    
    while intro:
        dt = intro_clock.tick(60)
        dt = 30 if dt >= 30 else dt

        background.draw_background(dt)
        
        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()
                
                play_text_btn.update_param()
                highscore_text_btn.update_param()
                quit_text_btn.update_param()
                credit_text_btn.update_param()
                how_text_btn.update_param()

                pause_btn.update_param()
                play_btn.update_param()
                unmute_btn.update_param()
                mute_btn.update_param()
                home_btn.update_param()
                '''
                
                textRect1.center = ((window_width/2), (window_height/8))#(window_height/12)
                textRect2.center = ((window_width/2), (window_height/8)+120)

                game_intro_rect1 = game_intro_img1.get_rect(midleft=(window_width/8, textRect1.bottom))
                game_intro_rect2 = game_intro_img2.get_rect(midleft=(window_width*6/8, textRect1.bottom))

                developerRect1.bottomright = (window_width-5, window_height-5-35)
                developerRect2.midbottom = (developerRect1.centerx, window_height-5)

        window.blit(textSurface1, textRect1)
        window.blit(textSurface2, textRect2)

        window.blit(developerSurface1, developerRect1)
        window.blit(developerSurface2, developerRect2)

        window.blit(game_intro_img1, game_intro_rect1)
        window.blit(game_intro_img2, game_intro_rect2)

        play_text_btn.draw_button(play_text_command, event_list)

        how_text_btn.draw_button(game_how_to, event_list)

        highscore_text_btn.draw_button(game_highscores, event_list)

        credit_text_btn.draw_button(game_credits, event_list)

        quit_text_btn.draw_button(quit_text_command, event_list)

        if mute:
            unmute_btn.draw_button(unmute_command, event_list)
        else:
            mute_btn.draw_button(mute_command, event_list)

        pg.display.update()

        textRect1.center = ((window_width/2), (window_height/8))#(window_height/12)
        textRect2.center = ((window_width/2), (window_height/8)+120)

        game_intro_rect1 = game_intro_img1.get_rect(midleft=(window_width/8, textRect1.bottom))
        game_intro_rect2 = game_intro_img2.get_rect(midleft=(window_width*6/8, textRect1.bottom))

        developerRect1.bottomright = (window_width-5, window_height-5-35)
        developerRect2.midbottom = (developerRect1.centerx, window_height-5)

def back_command():
    global highscore_menu, how_to_menu, credit_menu

    how_to_menu = False
    highscore_menu = False
    credit_menu = False

    #unmute_btn.update_param()
    #mute_btn.update_param()
    #play_text_btn.update_param()
    #highscore_text_btn.update_param()
    #quit_text_btn.update_param()


#Static background for menu options
#background_img = pg.image.load('.\\resources\\images\\background\\background.png').convert_alpha()

highscore_menu = False       
def game_highscores():
    global score_value, hs_dict, background_img, background_over
    global window_width, window_height, highscore_menu

    #background_over = pg.image.load(r'.\resources\images\text-background\game-intro.png').convert_alpha()
    
    back_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\back40.png').convert_alpha()
    back_btn_active_img = pg.image.load(r'.\resources\images\buttons\back56.png').convert_alpha()
    back_btn_inactive_x = 15
    back_btn_inactive_y = 20

    back_btn = OnlyImgButton(back_btn_inactive_img, back_btn_active_img,
                          back_btn_inactive_x, back_btn_inactive_y)

    textFont_head = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 50)
    textSurface_head1 = textFont_head.render('Score', True, (0,0,0))
    textSurface_head2 = textFont_head.render('Date, Time', True, (0,0,0))
    textRect_head1 = textSurface_head1.get_rect()
    textRect_head2 = textSurface_head2.get_rect()

    textFont_val = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 40)

    highscore_menu = True
    while highscore_menu:

        window.blit(background_img, (0,0))
        window.blit(background_over, (0,0))

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)
            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()

                play_text_btn.update_param()
                highscore_text_btn.update_param()
                quit_text_btn.update_param()
                credit_text_btn.update_param()
                how_text_btn.update_param()

                unmute_btn.update_param()
                mute_btn.update_param()
                '''
                
        textRect_head1.center = ((window_width*1.5/6),(window_height/8)+20)
        textRect_head2.center = ((window_width*4/6),(window_height/8)+20)
        window.blit(textSurface_head1, textRect_head1)
        window.blit(textSurface_head2, textRect_head2)

        linespace = 70
        if hs_dict:
            for key, val in hs_dict.items():
                textSurface_val1 = textFont_val.render(str(val[0]), True, (0,0,0))
                textRect_val1 = textSurface_val1.get_rect()
                textRect_val1.center = ((window_width*1.5/6),(window_height/8)+30+linespace)
                window.blit(textSurface_val1, textRect_val1)

                textSurface_val2 = textFont_val.render(val[1], True, (0,0,0))
                textRect_val2 = textSurface_val2.get_rect()
                textRect_val2.center = ((window_width*4/6),(window_height/8)+30+linespace)
                window.blit(textSurface_val2, textRect_val2)

                linespace += 70

        back_btn.draw_button(back_command, event_list)

        pg.display.update()

how_to_menu = False       
def game_how_to():
    global background_img, background_over
    global window_width, window_height, how_to_menu

    #background_over = pg.image.load(r'.\resources\images\text-background\game-intro.png').convert_alpha()
    
    back_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\back40.png').convert_alpha()
    back_btn_active_img = pg.image.load(r'.\resources\images\buttons\back56.png').convert_alpha()
    back_btn_inactive_x = 15
    back_btn_inactive_y = 20

    back_btn = OnlyImgButton(back_btn_inactive_img, back_btn_active_img,
                          back_btn_inactive_x, back_btn_inactive_y)

    linespace = 30
    paraspace = 40
    
    textFont_head = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 50)
    head_text = ['Player Movement', 'Player Weapons', 'Powerups']
    head_surface = []
    for txt in head_text:
        head_surface.append([textFont_head.render(txt, True, (0,0,0)),
                             textFont_head.render(txt, True, (0,0,0)).get_rect()])
    head_surface[0][1].midtop = (window_width/2, 40)
    
    textFont_para = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 40)
    para_text = ['Use keyboard arrow keys ', ' to move player', 'spaceship.',
                 'Use keyboard key ', ' to shoot lasers at enemy.' ,
                 'Use keyboard key ', ' to shoot missile at enemy when fully', 'charged.',
                 'Collect Powerups for different effects.',
                 ' - Gain 1 life.', ' - Freeze enemy for 3 seconds.', ' - Charge up the missile launcher.']
    para_surface = []
    for txt in para_text:
        para_surface.append([textFont_para.render(txt, True, (0,0,0)),
                             textFont_para.render(txt, True, (0,0,0)).get_rect()])
        
    para_surface[0][1].topleft = (50, head_surface[0][1].bottom+linespace)

    images = [
        [pg.image.load(r'.\resources\images\how-to\left72.png'),
         pg.Rect(para_surface[0][1].right, para_surface[0][1].top, 72, 72)],
        [pg.image.load(r'.\resources\images\how-to\up72.png'),
         pg.Rect(para_surface[0][1].right+90, para_surface[0][1].top, 72, 72)],
        [pg.image.load(r'.\resources\images\how-to\down72.png'),
         pg.Rect(para_surface[0][1].right+90+90, para_surface[0][1].top, 72, 72)],
        [pg.image.load(r'.\resources\images\how-to\right72.png'),
         pg.Rect(para_surface[0][1].right+90+90+90, para_surface[0][1].top, 72, 72)]
        ]

    para_surface[1][1].topleft = (images[3][1].right, head_surface[0][1].bottom+linespace)
    para_surface[2][1].topleft = (50, para_surface[1][1].bottom+linespace)
    head_surface[1][1].midtop = (window_width/2, para_surface[2][1].bottom+paraspace)
    para_surface[3][1].topleft = (50, head_surface[1][1].bottom+linespace)
    images.append(
        [pg.image.load(r'.\resources\images\how-to\a72.png'),
         pg.Rect(para_surface[3][1].right, para_surface[3][1].top, 72, 72)])
    para_surface[4][1].topleft = (images[4][1].right, para_surface[3][1].top)
    para_surface[5][1].topleft = (50, para_surface[4][1].bottom+linespace)
    images.append(
        [pg.image.load(r'.\resources\images\how-to\s72.png'),
         pg.Rect(para_surface[5][1].right, para_surface[5][1].top, 72, 72)])
    para_surface[6][1].topleft = (images[5][1].right, para_surface[5][1].top)
    para_surface[7][1].topleft = (50, para_surface[6][1].bottom+linespace)
    head_surface[2][1].midtop = (window_width/2, para_surface[7][1].bottom+paraspace)
    para_surface[8][1].topleft = (50, head_surface[2][1].bottom+linespace)
    images.append(
        [pg.image.load(r'.\resources\images\how-to\life72.png'),
         pg.Rect(50, para_surface[8][1].bottom+linespace, 72, 72)])
    images.append(
        [pg.image.load(r'.\resources\images\how-to\freeze72.png'),
         pg.Rect(50, images[6][1].bottom+linespace, 72, 72)])
    images.append(
        [pg.image.load(r'.\resources\images\how-to\charge72.png'),
         pg.Rect(50, images[7][1].bottom+linespace, 72, 72)])
    para_surface[9][1].topleft = (images[6][1].right, images[6][1].top)
    para_surface[10][1].topleft = (images[7][1].right, images[7][1].top)
    para_surface[11][1].topleft = (images[8][1].right, images[8][1].top)

    endy = para_surface[-1][1].bottom
    window_scroll = 20
    scrollbar_height = window_height/(endy/window_height)
    scrollbar_rect = pg.Rect(window_width-30, 40, 20, scrollbar_height)
    scrollbar_scroll = (window_height-scrollbar_rect.bottom-20)*(window_scroll)/(endy+50-window_height)
    
    how_to_menu = True
    while how_to_menu:

        window.blit(background_img, (0,0))
        window.blit(background_over, (0,0))

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)
            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()
                
                play_text_btn.update_param()
                highscore_text_btn.update_param()
                quit_text_btn.update_param()
                credit_text_btn.update_param()
                how_text_btn.update_param()

                unmute_btn.update_param()
                mute_btn.update_param()
                '''
                
            if event.type == pg.MOUSEWHEEL:
                if event.y < 0:
                    if para_surface[-1][1].bottom > window_height-50:
                        for surface, rect in head_surface:
                            rect.y += event.y*window_scroll
                        for surface, rect in para_surface:
                            rect.y += event.y*window_scroll
                        for surface, rect in images:
                            rect.y += event.y*window_scroll
                        scrollbar_rect.y -= event.y*scrollbar_scroll
                        if scrollbar_rect.bottom > window_height-20:
                            scrollbar_rect.bottom = window_height-20
                elif event.y > 0:
                    if head_surface[0][1].top < 40:
                        for surface, rect in head_surface:
                            rect.y += event.y*window_scroll
                        for surface, rect in para_surface:
                            rect.y += event.y*window_scroll
                        for surface, rect in images:
                            rect.y += event.y*window_scroll
                        scrollbar_rect.y -= math.floor(event.y*scrollbar_scroll)
                        if scrollbar_rect.bottom < scrollbar_height+40:
                            scrollbar_rect.bottom = scrollbar_height+40

        for surface, rect in head_surface:
            rect.centerx = window_width/2
            window.blit(surface, rect)
            
        for surface, rect in para_surface:   
            window.blit(surface, rect)

        for img, rect in images:   
            window.blit(img, rect)

        back_btn.draw_button(back_command, event_list)

        scrollbar_rect.h = window_height/(endy/window_height)
        scrollbar_rect.left = window_width-30

        pg.draw.rect(window, (0,0,0), scrollbar_rect)
        
        pg.display.update()

credit_menu = False       
def game_credits():
    global background_img, background_over
    global window_width, window_height, credit_menu

    #background_over = pg.image.load(r'.\resources\images\text-background\game-intro.png').convert_alpha()
    
    back_btn_inactive_img = pg.image.load(r'.\resources\images\buttons\back40.png').convert_alpha()
    back_btn_active_img = pg.image.load(r'.\resources\images\buttons\back56.png').convert_alpha()
    back_btn_inactive_x = 15
    back_btn_inactive_y = 20

    back_btn = OnlyImgButton(back_btn_inactive_img, back_btn_active_img,
                          back_btn_inactive_x, back_btn_inactive_y)

    '''
    textFont_head = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 50)
    textSurface_head1 = textFont_head.render('Score', True, (0,0,0))
    textSurface_head2 = textFont_head.render('Date, Time', True, (0,0,0))
    textRect_head1 = textSurface_head1.get_rect()
    textRect_head2 = textSurface_head2.get_rect()
    '''
    
    textFont_entry = freetype.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 20)
    textFont_entry_underline = freetype.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 20)
    textFont_entry_underline.underline = True

    linespace = 12
    headspace = 20

    credit_img = [
        {'link' : "https://www.flaticon.com/authors/icongeek26", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/freepik", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/bqlqn", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/darius-dan", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/fjstudio", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/smashicons", 'rect' : None, 'underline' : False},
        {'link' : "http://fontawesome.io/", 'rect' : None, 'underline' : False},
        {'link' : "http://www.creaticca.com/", 'rect' : None, 'underline' : False},
        {'link' : "https://creativemarket.com/eucalyp", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/kirill-kazachek", 'rect' : None, 'underline' : False},
        {'link' : "https://www.flaticon.com/authors/itim2101", 'rect' : None, 'underline' : False}
        ]

    credit_sound = [
        {'link' : 'https://freesound.org/people/LittleRobotSoundFactory/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/BigKahuna360/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/Jace/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/qubodup/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/Bird_man/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/asdftekno/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/JustInvoke/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/Mozfoo/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/Robinhood76/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/alexmol/', 'rect' : None, 'underline' : False},
        {'link' : 'https://freesound.org/people/Capashen/', 'rect' : None, 'underline' : False}
        ]

    start_pos = [100, 0]

    window_scroll = 20
    
    credit_menu = True
    while credit_menu:

        window.blit(background_img, (0,0))
        window.blit(background_over, (0,0))

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)
            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()

                play_text_btn.update_param()
                highscore_text_btn.update_param()
                quit_text_btn.update_param()
                credit_text_btn.update_param()
                how_text_btn.update_param()

                unmute_btn.update_param()
                mute_btn.update_param()
                '''
                
        prevrect_img = pg.Rect(*start_pos, 50, 50)
        for credit in credit_img:
            if credit['underline']:
                surface, rect = textFont_entry_underline.render(credit['link'], (0,0,0))
            else:
                surface, rect = textFont_entry.render(credit['link'], (0,0,0))
            rect.topleft = (prevrect_img.left, prevrect_img.bottom+linespace)
            credit['rect'] = rect
            prevrect_img = rect
            window.blit(surface, rect)

        prevrect_sound = pg.Rect(start_pos[0], prevrect_img.bottom, 50, 50)
        for credit in credit_sound:
            if credit['underline']:
                surface, rect = textFont_entry_underline.render(credit['link'], (0,0,0))
            else:
                surface, rect = textFont_entry.render(credit['link'], (0,0,0))
            rect.topleft = (prevrect_sound.left, prevrect_sound.bottom+linespace)
            credit['rect'] = rect
            prevrect_sound = rect
            window.blit(surface, rect)

        for event in event_list:
            if event.type == pg.MOUSEWHEEL:
                if event.y < 0:
                    if prevrect_sound.bottom > window_height-50:
                        start_pos[1] += event.y*window_scroll
                if event.y > 0:
                    if start_pos[1] < 0:
                        start_pos[1] += event.y*window_scroll

            if event.type == pg.MOUSEMOTION:
                for credit in credit_img+credit_sound:
                    if credit['rect'].collidepoint(event.pos):
                        credit['underline'] = True
                        pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_HAND)
                    else:
                        credit['underline'] = False
                        #pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_ARROW)
                
            if event.type == pg.MOUSEBUTTONUP:
                for credit in credit_img+credit_sound:
                    if credit['rect'].collidepoint(event.pos) and event.button == 1:
                        webbrowser.open_new_tab(credit['link'])

        if not any([x['underline'] for x in credit_img+credit_sound]):
            pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_ARROW)

        '''
        mouse_pos = pg.mouse.get_pos()
        mouse_click = pg.mouse.get_pressed()
        for credit in credit_img+credit_sound:
            if credit['rect'].collidepoint(mouse_pos):
                credit['underline'] = True
                if mouse_click[0]:
                    print(mouse_click)                
            else:
                credit['underline'] = False
        '''
        
        back_btn.draw_button(back_command, event_list)
        
        pg.display.update()

def game_over(dt, screenshot):
    global window_width, window_height, pause_txt_background, intro

    textBackground = pg.image.load(r'F:\PYTHON\battleship_game\resources\images\text-background\home-background1920.png').convert_alpha()
    textBackgroundRect = textBackground.get_rect()
    textBackgroundRect.center = ((window_width/2), (window_height/2))

    textFont = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Bold.ttf', 100)
    textSurface = textFont.render('Game Over', True, (0,0,0))
    textRect = textSurface.get_rect()
    textRect.midleft = (window_width, (textBackgroundRect.top + textBackgroundRect.height*2/3))

    textFont2 = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-SemiBold.ttf', 80)
    textSurface2 = textFont2.render('Score : ' + str(score_value), True, (0,0,0))
    textRect2 = textSurface2.get_rect()
    textRect2.midbottom = (window_width/2, (textBackgroundRect.top + textBackgroundRect.height*1/3))

    while True:

        event_list = pg.event.get()
        for event in event_list:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)
            if event.type == pg.VIDEORESIZE:
                resize(event)
                '''
                window_width, window_height = event.size
                window_rect = window.get_rect()

                play_text_btn.update_param()
                highscore_text_btn.update_param()
                quit_text_btn.update_param()
                credit_text_btn.update_param()
                how_text_btn.update_param()

                unmute_btn.update_param()
                mute_btn.update_param()
                '''
                
        window.blit(pg.transform.scale(screenshot, (window_width, window_height)), (0,0))
        window.blit(textBackground, textBackgroundRect)
        window.blit(textSurface, textRect)
        textRect2.centerx = window_width/2
        window.blit(textSurface2, textRect2)

        change = 0.2*dt
        if textRect.left - change < 0:
            multiplier = 10 ** 0
            change = math.ceil(change * multiplier) / multiplier

        textRect.left -= change

        if textRect.right <= -10:
            intro = True
            reset()
            break

        pg.display.update()
        

#Function to decrease life of player on collision with enemy or enemy lasers
player_dmg_sound = mixer.Sound(r'.\resources\sounds\whoosh-sci-fi-short.wav')
def player_collision(dt):
    global enemy_small, enemy_medium, player_rect, player_health, mute, score_value
    global enemy_large, player_dmg_sound, mute, powerups, channels

    for enemy in enemy_small:
        if (player_rect.colliderect(enemy_small[enemy]['rect']) and
            enemy_small[enemy]['alive']):
            player_health -= 1
            enemy_small[enemy]['alive'] = False
            score_value += 1
            if mute == False:
                channels[1].play(explosion_sound)

        if (player_rect.colliderect(enemy_small[enemy]['laser_rect']) and
            enemy_small[enemy]['laser_draw']):
            player_health -= 1
            enemy_small[enemy]['laser_draw'] = False
            if mute == False:
                channels[9].play(player_dmg_sound)

    for laser in enemy_medium.lasers:
        if player_rect.colliderect(enemy_medium.lasers[laser]['laser1rect']):
            enemy_medium.lasers[laser]['cur_laser1_x'] = enemy_medium.lasers[laser]['cur_laser1_y'] = -50
            player_health -= 1
            if mute == False:
                channels[9].play(player_dmg_sound)
        if player_rect.colliderect(enemy_medium.lasers[laser]['laser2rect']):
            enemy_medium.lasers[laser]['cur_laser2_x'] = enemy_medium.lasers[laser]['cur_laser2_y'] = -50
            player_health -= 1
            if mute == False:
                channels[9].play(player_dmg_sound)

    for laser in enemy_large.lasers:
        if player_rect.colliderect(enemy_large.lasers[laser]['laser1rect']):
            enemy_large.lasers[laser]['laser1rect'].x = enemy_large.lasers[laser]['laser1rect'].y = -50
            player_health -= 1
            if mute == False:
                channels[9].play(player_dmg_sound)

    for plasma in enemy_large.plasmas:
        if player_rect.colliderect(enemy_large.plasmas[plasma]['rect']):
            enemy_large.plasmas[plasma]['cur_x'] = enemy_large.plasmas[plasma]['cur_y'] = -50
            player_health -= 1
            if mute == False:
                channels[9].play(player_dmg_sound)

    for item in powerups.powerups:
        if player_rect.colliderect(powerups.powerups[item]['rect']):
            powerups.powerups[item]['func'](dt)

    
def update_highscore():
    global hs_dict, score_value

    if len(hs_dict) < 5:
        hs_dict[len(hs_dict)+1] = [score_value, datetime.datetime.now().strftime('%d-%b-%Y, %I:%M:%S %p')]
    elif len(hs_dict) == 5:
        if score_value >= hs_dict[list(hs_dict.keys())[-1]][0]:
            hs_dict[list(hs_dict.keys())[-1]] = [score_value, datetime.datetime.now().strftime('%d-%b-%Y, %I:%M:%S %p')]

    hs_dict = {k: v for k, v in sorted(hs_dict.items(), key=lambda item: item[1][0], reverse=True)}

    with open('highscores.pickle', 'wb') as fh:
        pickle.dump(hs_dict, fh)

#Resize and rearrange various surfaces
def resize(event):
    global window_width, window_height, window_rect, pause_btn, play_btn, charge_rect
    global rocket_rect, unmute_btn, mute_btn ,home_btn, play_text_btn, highscore_text_btn
    global quit_text_btn, credit_text_btn, how_text_btn, enemy_medium, enemy_large


    player_update(event)

    window_width, window_height = event.size
    window_rect = window.get_rect()

    update_player_health_rect()

    pause_btn.update_param()
    play_btn.update_param()
    unmute_btn.update_param()
    mute_btn.update_param()
    home_btn.update_param()

    play_text_btn.update_param()
    highscore_text_btn.update_param()
    quit_text_btn.update_param()
    credit_text_btn.update_param()
    how_text_btn.update_param()

    charge_rect.bottomleft = (10, window_height-10)
    rocket_rect.center = charge_rect.center

    enemy_medium.resize()
    enemy_large.resize()
    
    
#Reset game and make it ready for new game
def reset():
    global score_value, cur_player_x, cur_player_y, player_img_w, player_img_h
    global lasers, reset_game, enemy_medium, isinit_enemy_small_last
    global spawn_medium_enemy_trigger1, spawn_medium_enemy_trigger2
    global player_health, playerX_change, playerY_change, lvl_value, player_max_health
    global enemy_large, charge_value, missile_explosion_dict, powerups, enemy_small_killed
    
    if score_value > 0:
        update_highscore()
    score_value = 0

    lvl_value = 1

    charge_value = 0

    player_health = player_max_health

    cur_player_x = window_width/2 - player_img_w/2
    cur_player_y = ((window_height/player_img_h)-1.5)*player_img_h
    playerX_change = 0
    playerY_change = 0

    init_enemy_small_pos()
    isinit_enemy_small_last = False
    enemy_small_killed = 0
    
    lasers.clear()

    enemy_medium.__init__()
    spawn_medium_enemy_trigger1 = False
    spawn_medium_enemy_trigger2 = False

    enemy_large.__init__()
    spawn_large_enemy_trigger1 = False
    spawn_large_enemy_trigger2 = False

    for explosion in missile_explosion_dict:
        missile_explosion_dict[explosion][1].center = (-1000, -1000)

    powerups.__init__()

    reset_game = False

#Mainloop clock
clock = pg.time.Clock()

fps_font = pg.font.Font(r'.\resources\fonts\Open_Sans\OpenSans-Regular.ttf', 20) 
reset_game = False
running = True


#MAIN GAME LOOP
#All gameplay objects are drawn in this loop.
#All evnets(like mouse click and key press) during gameplay are handled in this loop. 
while running:
    
    dt = clock.tick(60)
    if dt > 30:
        dt = 30
    
    fps_surface = fps_font.render(f'{clock.get_fps():.2f}', True, (0,0,0))
    window.fill((255,255,255))

    if intro:
        game_intro()
    if reset_game:
        reset()

    background.draw_background(dt)

    #EVENT HANDLING
    event_list = pg.event.get()
    for event in event_list:

        if event.type == pg.QUIT:
            if score_value:
                update_highscore()
            running = False
            #pg.quit()
            #sys.exit()

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                playerX_change = -player_xspeed*dt
            if event.key == pg.K_RIGHT:
                playerX_change = player_xspeed*dt
            if event.key == pg.K_UP:
                playerY_change = -player_yspeed*dt
            if event.key == pg.K_DOWN:
                playerY_change = player_yspeed*dt

            if event.key == pg.K_a:
                add_laser()
            if event.key == pg.K_s:
                if charge_value == 12:
                    if mute == False:
                        channels[4].play(missile_launch_sound)
                    missile_draw = True
                    missile_rect.midbottom = player_rect.midtop
                    missile_cur_x = missile_rect.x
                    missile_cur_y = missile_rect.y
                    charge_value = 0
                
        if event.type == pg.KEYUP:
            if event.key == pg.K_LEFT or event.key == pg.K_RIGHT:
                pressed = pg.key.get_pressed()
                if pressed[pg.K_RIGHT] or pressed[pg.K_LEFT]:
                    playerX_change = playerX_change
                else:
                    playerX_change = 0
            if event.key == pg.K_UP or event.key == pg.K_DOWN:
                pressed = pg.key.get_pressed()
                if pressed[pg.K_UP] or pressed[pg.K_DOWN]:
                    playerY_change = playerY_change
                else:
                    playerY_change = 0

        if event.type == pg.VIDEORESIZE:
            resize(event)
            '''
            player_update(event)

            window_width, window_height = event.size
            window_rect = window.get_rect()

            update_player_health_rect()

            pause_btn.update_param()
            play_btn.update_param()
            unmute_btn.update_param()
            mute_btn.update_param()
            home_btn.update_param()

            charge_rect.bottomleft = (10, window_height-10)
            rocket_rect.center = charge_rect.center
            '''

    powerups.draw(dt)

    draw_charge_quantity()
    
    #Drawing flashes from payer cannon
    pressed = pg.key.get_pressed()
    if pressed[pg.K_a]:
        num = draw_flash(player_rect, num)
       
    background_objects.draw_objects(dt)
    
    draw_player()

    #if str(lvl_value)[-1] == '9' and score_value%20 == 0:
     #   increase_lvl()
        
    #Condition to spawn large enemy
    #if lvl_value and lvl_value%5 == 0:
    if (lvl_value and
        enemy_small_killed >= 20 and
        (str(lvl_value)[-1] == '4' or
         str(lvl_value)[-1] == '9')):
        if not isinit_enemy_small_last:
            isinit_enemy_small_last = True
            spawn_large_enemy_trigger1 = True
            init_enemy_small_last()

    if spawn_large_enemy_trigger1 and not spawn_large_enemy_trigger2:
        draw_enemy_small_last(dt)

    if spawn_large_enemy_trigger1 and spawn_large_enemy_trigger2:
        enemy_large.draw_enemy(dt, event_list)
    
    #Condition to spawn medium enemy
    if (enemy_small_killed >= 20 and
        str(lvl_value)[-1] != '9' and str(lvl_value)[-1] != '4'):
        if not isinit_enemy_small_last:
            isinit_enemy_small_last = True
            spawn_medium_enemy_trigger1 = True
            init_enemy_small_last()    
        
    if spawn_medium_enemy_trigger1 and not spawn_medium_enemy_trigger2:
        draw_enemy_small_last(dt)

    if spawn_medium_enemy_trigger1 and spawn_medium_enemy_trigger2:
        enemy_medium.draw_enemy(dt, event_list)

    
    if not spawn_medium_enemy_trigger1 and not spawn_large_enemy_trigger1:
        draw_enemy_small(dt)

    draw_laser(dt)

    #if missile_draw:
    draw_missile(dt)

    draw_score(scoreX, scoreY)
    draw_lvl()

    screenshot = pg.Surface((window_width, window_height))
    screenshot.blit(window, (0,0))
    
    home_btn.update_param()
    home_btn.draw_button(home_command, event_list, screenshot)
    
    pause_btn.update_param()
    pause_btn.draw_button(pause_command, event_list, screenshot)

    mute_btn.btn_inactiveX = window_width - mute_btn_inactive_img.get_width() - 15
    mute_btn.btn_inactiveY = 20 + mute_btn_inactive_img.get_height() + 20
    mute_btn.update_param()
    unmute_btn.btn_inactiveX = window_width - unmute_btn_inactive_img.get_width() - 15
    unmute_btn.btn_inactiveY = 20 + unmute_btn_inactive_img.get_height() + 20
    unmute_btn.update_param()
    if mute:
        unmute_btn.draw_button(unmute_command, event_list)
    else:
        mute_btn.draw_button(mute_command, event_list)

    if player_health < 1:
        game_over(dt, screenshot)

    player_collision(dt)

    window.blit(fps_surface, (5, window_height-150))
    
    pg.display.update()
    #END OF GAME LOOP


pg.quit()
