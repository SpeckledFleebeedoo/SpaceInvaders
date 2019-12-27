import pygame as pg
import numpy as np
import sys
from random import randint

class Board:
    def __init__(self, screen, score = 0):
        self.screen = screen
        pg.display.set_caption("Space Invaders")

        self.UI = Interface(screen, score)

        #Create enemies, different sizes for each species
        self.enemies = np.array([
            [Enemy(self.screen, "Alien3", (28+i*70,20,32,32), 30) for i in range(11)],
            [Enemy(self.screen, "Alien1", (22+i*70,90,44,32), 20) for i in range(11)],
            [Enemy(self.screen, "Alien1", (22+i*70,160,44,32), 20) for i in range(11)],
            [Enemy(self.screen, "Alien2", (20+i*70,230,48,32), 10) for i in range(11)],
            [Enemy(self.screen, "Alien2", (20+i*70,300,48,32), 10) for i in range(11)]
        ])
        
        #Set outer rows
        self.rightmostrow = 10
        self.leftmostrow = 0

        #Create player
        self.player = Player(self.screen)

        #Set starting enemy move direction
        self.direction = "r"

        #Number of enemies killed and gamespeed
        self.enemieskilled = 0
        self.waittime = 60

        self.enemybullets = []
        self.lastenemyshottime = -1000

    #Main game loop
    def run(self):
        while True:
            #Clear screen
            self.screen.fill(Background)
            
            #Check for events, quit if necessary
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)
            
            #Check if any bullet hits any enemy, delete bullet and kill enemy if true
            for row in self.enemies:
                for enemy in row:
                    for i, bullet in enumerate(self.player.bullets):
                        if enemy.rect.colliderect(bullet) == True and enemy.isdead == False:
                            del self.player.bullets[i]
                            enemy.isdead = True
                            self.enemieskilled += 1
                            self.waittime -= 1
                            self.UI.score += enemy.value
            
            #Check if any enemy bullet hits the player
            for i, bullet in enumerate(self.enemybullets):
                if self.player.rect.colliderect(bullet) == True:
                    self.UI.health -= 1
                    del self.enemybullets[i]
                    screen.fill(Red)
            
            #Check player health, lose if 0
            if self.UI.health <= 0:
                self.lose()
            
            #Win if all enemies killed
            if self.enemieskilled == 55:
                self.win()

            #Lose if any enemy advances too far
            for row in self.enemies:
                for enemy in row:
                    if enemy.isdead == False and enemy.rect.centery > 830:
                        self.lose()

            #Player controls
            keys=pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                self.player.move("l")
            if keys[pg.K_RIGHT]:
                self.player.move("r")
            if keys[pg.K_SPACE]:
                self.player.shoot()

            #Find right- and leftmost living enemies TODO: Change
            self.findrightmostliving()
            self.findleftmostliving()

            #Reverse enemies if outermost living enemy hits edge and move them down
            if self.enemies[0,self.rightmostrow].rect.centerx >= 875:
                self.direction = "l"
                self.movealldown()

            if self.enemies[0,self.leftmostrow].rect.centerx <= 25:
                self.direction = "r"
                self.movealldown()
            
            #Shoot if possible
            self.enemyshoot()

            #Move all enemies
            for row in self.enemies:
                for enemy in row:
                    if enemy.isdead == False:
                        enemy.move(self.direction)
            
            #Update and draw enemy bullets
            self.updatebullets()

            #Update player position and bullets
            self.player.draw()
            self.player.updateBullets()

            self.UI.updateUI()

            #Refresh display, game speed control
            pg.display.flip()
            pg.time.wait(int(self.waittime/3))
    
    #Actions when game is won
    def win(self):
        self.screen.fill(Green)
        pg.display.flip()        
        pg.time.wait(2000)
        board.reset()
    
    #Actions when game is lost
    def lose(self):
        self.lost = True
        self.screen.fill(Red)
        pg.display.flip()
        pg.time.wait(2000)
        pg.quit()
        sys.exit(0)
    
    def reset(self):
        board.__init__(self.screen, self.UI.score)

    #Moves all enemies down
    def movealldown(self):
        for row in self.enemies:
            for enemy in row:
                enemy.movedown()
    
    #Pick an enemy to shoot
    def enemyshoot(self):
        currenttime = pg.time.get_ticks()
        if currenttime - self.lastenemyshottime >= 800:
            colnum = randint(self.leftmostrow, self.rightmostrow)
            coltofire = self.enemies[:, colnum] 
            lowest = 4
            while lowest >= 0:
                enemy = coltofire[lowest]
                if enemy.isdead == False:
                    enemy.shoot(self.enemybullets)
                    self.lastenemyshottime = currenttime
                    break
                else:
                    lowest -= 1
                if lowest == 0:
                    self.lastenemyshottime = currenttime - 1000
    
    def updatebullets(self):
        for i, bullet in enumerate(self.enemybullets):
            bullet.move()
            if bullet.rect.centery > 900:
                del self.enemybullets[i]

    #Finds row rightmost living enemy is in
    def findrightmostliving(self):
        while self.rightmostrow >= 0:
            numdead = 0
            rightcol = self.enemies[:, self.rightmostrow]
            for enemy in rightcol:
                if enemy.isdead == True:
                    numdead += 1
            if numdead == 5:
                self.rightmostrow -= 1
            else:
                break
    
    #Finds row leftmost living enemy is in
    def findleftmostliving(self):
        while self.leftmostrow <= 10:
            numdead = 0
            leftcol = self.enemies[:, self.leftmostrow]
            for enemy in leftcol:
                if enemy.isdead == True:
                    numdead += 1
            if numdead == 5:
                self.leftmostrow += 1
            else:
                break

class Enemy:
    #Tag for dead enemies
    isdead = False
    timer = 0

    def __init__(self, screen, species, position, value):
        self.screen = screen

        #Draw rect and add correct sprite
        self.rect = pg.draw.rect(self.screen, Background, position)
        self.frames = [pg.image.load("Sprites/"+species+"_1.png"), pg.image.load("Sprites/"+species+"_2.png")]
        self.currentframe = 0
        self.image = self.frames[self.currentframe]
        self.screen.blit(self.image, self.rect)

        #Value when killed in points
        self.value = value

    #Moves down enemies
    def movedown(self):
        self.rect.move_ip((0, 30))
    
    #Moves enemies in given direction
    def move(self, direction):
        if direction == "l":
            move = (-1,0)
        elif direction == "r":
            move = (1,0)
        self.rect.move_ip(move)
        self.rect = pg.draw.rect(self.screen, Background, self.rect)
        self.updateanimation()
        self.screen.blit(self.image, self.rect)

    def shoot(self, bulletslist):
        bulletslist.append(Bullet(self.screen, "alien", (self.rect.centerx, self.rect.centery)))

    def updateanimation(self):
        now = pg.time.get_ticks()
        if now - self.timer > 1000.0/2:
            self.currentframe = (self.currentframe+1) % len(self.frames)
            self.timer = now
            self.image = self.frames[self.currentframe]

class Player:
    def __init__(self, screen):
        self.screen = screen

        #Draw player
        self.rect = pg.draw.rect(self.screen, Background, (450, 850, 52, 32))
        self.image = pg.image.load("Sprites/Turret.png")
        self.screen.blit(self.image, self.rect)

        #List of bullets and time since last shot
        self.bullets = []
        self.lastshottime = -1000
    
    #Draw player after each update
    def draw(self):
        self.rect = pg.draw.rect(self.screen, Background, self.rect)
        self.screen.blit(self.image, self.rect)

    #Move and draw all bullets
    def updateBullets(self):
        for i, bullet in enumerate(self.bullets):
            bullet.move()
            if bullet.rect.centery < 0:
                del self.bullets[i]
    
    #Move player in given direction
    def move(self, direction):
        if direction == "l" and self.rect.centerx >= 25:
            move = (-4,0)
        elif direction == "r" and self.rect.centerx <= 875:
            move = (4,0)
        else:
            move = (0,0)
        self.rect.move_ip(move)
    
    #Shoot bullet from player
    def shoot(self):
        currenttime = pg.time.get_ticks()
        if currenttime - self.lastshottime >= 700:
            self.bullets.append(Bullet(self.screen, "player", (self.rect.centerx, self.rect.centery)))
            self.lastshottime = currenttime

class Bullet:
    def __init__(self, screen, faction, origin):
        self.screen = screen

        #Set starting position and size
        origin = (origin[0], origin[1], 5, 15)

        #Set direction, TODO: Add enemy bullets
        if faction == "player":
            self.direction = (0, -20)
            self.colour = Green
        elif faction == "alien":
            self.direction = (0, 5)
            self.colour = White
        
        #Draw bullet
        self.rect = pg.draw.rect(self.screen, self.colour, origin)
    
    #Update location and draw bullet
    def move(self):
        self.rect.move_ip(self.direction)
        self.rect = pg.draw.rect(self.screen, self.colour, self.rect)

class Interface:
    def __init__(self, screen, score):

        #Set defaults
        self.screen = screen
        self.health = 3
        self.score = score

        #Load all images
        self.scoretext = pg.image.load("UI/ScoreText.png")
        self.healthimg = pg.image.load("Sprites/Turret.png")
        self.numbers = {
            "0":pg.image.load("UI/0.png"), 
            "1":pg.image.load("UI/1.png"), 
            "2":pg.image.load("UI/2.png"),
            "3":pg.image.load("UI/3.png"),
            "4":pg.image.load("UI/4.png"),
            "5":pg.image.load("UI/5.png"),
            "6":pg.image.load("UI/6.png"),
            "7":pg.image.load("UI/7.png"),
            "8":pg.image.load("UI/8.png"),
            "9":pg.image.load("UI/9.png")
            }
        
        #Create rect for score label
        self.scoretextrect = pg.draw.rect(self.screen, Background, (5,5,148,28))

    #Update all UI elements
    def updateUI(self):
        self.drawscore()
        self.drawhealth()
    
    #Update score counter
    def drawscore(self):

        #Draw score text on score rect
        self.screen.blit(self.scoretext, self.scoretextrect)
        
        #Number positioning
        position = 5

        #Iterate over numbers in score value
        for num in str(self.score):
            image = self.numbers[num]
            width  = 20

            #Set smaller width for numbe r1
            if num == "1":
                width = 12
            
            #Create rect and draw image on rect
            rect = pg.draw.rect(self.screen, Background, (position, 40, width, 28))
            self.screen.blit(image, rect)

            #Increase position counter by width + space for next number
            position += 12 + width
    
    #Update health counter
    def drawhealth(self):

        #Health indicator positioning
        position = 5

        #Iterate over amount of health, draw turret for each
        for _ in range(self.health):
            rect = pg.draw.rect(self.screen, Background, (position, 863, 52, 32))
            self.screen.blit(self.healthimg, rect)
            position += 62

#Default colours
Red = (255,0,0)
Green = (0,255,0)
White = (255,255,255)
Background = (0,0,0)

#Init screen and start game
screen = pg.display.set_mode((900, 900))
board = Board(screen)
board.run()