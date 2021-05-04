# Importing the modules required for the Pygame
from pygame import *
import sys
from random import choice

# Path to be used for the Game Files
basePath = r'C:\Users\kunal\PycharmProjects\PyGame'
fontPath = basePath + '/gamefiles/font/'
imagesPath = basePath + '/gamefiles/images/'

# Outline Color Combinations
white = (255, 255, 255)
purple = (203, 0, 255)
red = (237, 28, 36)

# Setting up the Screen display
screen = display.set_mode((800, 600))
# Fonts to be used for the Game
fonts = fontPath + 'gamefonts.ttf'
# Loading Images
image_names = ['hero',
               'enemy1', 'enemy2',
               'enemy3', 'enemy4',
               'explosion',
               'rocket',
               'enemyRocket']

IMAGES = {name: image.load(imagesPath + '{}.png'.format(name)).convert_alpha()
          for name in image_names}

# Initial Position for the Blockers
blockersPosition = 420
# Enemy Position
enemyPosition = 100


class Hero(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['hero']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 50:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 700:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Rocket(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1', '1'],
                  1: ['2', '2'],
                  2: ['3', '3'],
                  3: ['4', '4'],
                  }
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in
                      images[self.row])
        self.images.append(transform.scale(img1, (35, 35)))
        self.images.append(transform.scale(img2, (35, 35)))


class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 100
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0

            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                self.moveNumber += 1

            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column]
                        for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col]
                        for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ['', '', '', '']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class HeroExplosion(sprite.Sprite):
    def __init__(self, hero, *groups):
        super(HeroExplosion, self).__init__(*groups)
        self.image = IMAGES['hero']
        self.rect = self.image.get_rect(topleft=(hero.rect.x, hero.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['hero']
        self.image = transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 512)
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Space Invaders')
        self.screen = screen
        self.background = image.load(imagesPath + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False

        self.enemyPosition = enemyPosition
        self.titleText = Text(fonts, 55, 'Space Invaders', red, 150, 80)
        self.titleText2 = Text(fonts, 25, 'Press any key to continue', white,
                               201, 170)
        self.gameOverText = Text(fonts, 50, 'Game Over', white, 250, 270)
        self.nextRoundText = Text(fonts, 50, 'Next Round', white, 240, 270)
        self.enemy1Text = Text(fonts, 25, '   =  10 pts', white, 360, 230)
        self.enemy2Text = Text(fonts, 25, '   =  20 pts', white, 360, 280)
        self.enemy3Text = Text(fonts, 25, '   =  20 pts', white, 360, 330)
        self.enemy4Text = Text(fonts, 25, '   =  30 pts', white, 360, 380)
        self.scoreText = Text(fonts, 20, 'Score', white, 5, 5)
        self.livesText = Text(fonts, 20, 'Lives ', white, 640, 5)
        self.instructionsText1 = Text(fonts, 25, '<- Move Hero ->', white, 295, 450)
        self.instructionsText2 = Text(fonts, 25, 'Spacebar to Shoot', white, 265, 500)

        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

    def reset(self, score):
        self.player = Hero()
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.rockets = sprite.Group()
        self.enemyRockets = sprite.Group()
        self.create_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies,
                                       self.livesGroup)
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.heroTimer = time.get_ticks()
        self.score = score
        self.makeNewHero = False
        self.heroAlive = True

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(5):
            for column in range(8):
                blocker = Blocker(10, purple, row, column)
                blocker.rect.x = 60 + (200 * number) + (column * blocker.width)
                blocker.rect.y = blockersPosition + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    @staticmethod
    def should_exit(evt):
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.rockets) == 0 and self.heroAlive:
                        if self.score < 1000:
                            rocket = Rocket(self.player.rect.x + 23,
                                            self.player.rect.y + 5, -1,
                                            15, 'rocket', 'center')
                            self.rockets.add(rocket)
                            self.allSprites.add(self.rockets)
                        else:
                            leftrocket = Rocket(self.player.rect.x + 8,
                                                self.player.rect.y + 5, -1,
                                                15, 'rocket', 'left')
                            rightrocket = Rocket(self.player.rect.x + 38,
                                                 self.player.rect.y + 5, -1,
                                                 15, 'rocket', 'right')
                            self.rockets.add(leftrocket)
                            self.rockets.add(rightrocket)
                            self.allSprites.add(self.rockets)

    def create_enemies(self):
        enemies = EnemiesGroup(10, 4)
        for row in range(4):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyRockets.add(
                Rocket(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                       'enemyRocket', 'center'))
            self.allSprites.add(self.enemyRockets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 40,
                  1: 30,
                  2: 20,
                  3: 10,
                  }

        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.enemy1 = IMAGES['enemy4']
        self.enemy1 = transform.scale(self.enemy1, (40, 40))
        self.enemy2 = IMAGES['enemy3']
        self.enemy2 = transform.scale(self.enemy2, (40, 40))
        self.enemy3 = IMAGES['enemy2']
        self.enemy3 = transform.scale(self.enemy3, (40, 40))
        self.enemy4 = IMAGES['enemy1']
        self.enemy4 = transform.scale(self.enemy4, (40, 40))
        self.screen.blit(self.enemy1, (318, 220))
        self.screen.blit(self.enemy2, (318, 270))
        self.screen.blit(self.enemy3, (318, 320))
        self.screen.blit(self.enemy4, (318, 370))

    def check_collisions(self):
        sprite.groupcollide(self.rockets, self.enemyRockets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.rockets,
                                         True, True).keys():
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for player in sprite.groupcollide(self.playerGroup, self.enemyRockets,
                                          True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            HeroExplosion(player, self.explosionsGroup)
            self.makeNewHero = True
            self.heroTimer = time.get_ticks()
            self.heroAlive = False

        sprite.groupcollide(self.rockets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyRockets, self.allBlockers, True, True)

    def create_new_hero(self, createHero, currentTime):
        if createHero and (currentTime - self.heroTimer > 900):
            self.player = Hero()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewHero = False
            self.heroAlive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.instructionsText1.draw(self.screen)
                self.instructionsText2.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Only create blockers on a new game, not a new round
                        self.allBlockers = sprite.Group(self.make_blockers(0),
                                                        self.make_blockers(1),
                                                        self.make_blockers(2),
                                                        self.make_blockers(3))
                        self.livesGroup.add(self.life1, self.life2, self.life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(fonts, 20, str(self.score),
                                               purple, 85, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                    if currentTime - self.gameTimer > 3000:
                        # Move enemies closer to bottom
                        self.reset(self.score)
                        self.gameTimer += 3000

                else:
                    currentTime = time.get_ticks()
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(fonts, 20, str(self.score), purple,
                                           85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_hero(self.makeNewHero, currentTime)
                    self.make_enemies_shoot()

            elif self.gameOver:
                currentTime = time.get_ticks()
                self.enemyPosition = enemyPosition
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()