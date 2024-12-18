import pygame
import random
import math
import os
from pygame import mixer
from typing import List, Tuple

# initialization Pygame
pygame.init()
mixer.init()

class SpaceInvadersGame:
    UPDATE_INTERVAL = 8  # about 120 FPS
    
    def __init__(self):
        # screen settings
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        pygame.display.set_caption("Space Invaders")
        
        # initialization game components
        self.player = Player(self.screen_width // 2, self.screen_height - 50, 
                           30, 30, self.screen_width, self.screen_height)
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.stars: List[Star] = []
        self.engine_trails: List[EngineTrail] = []
        self.smoke_particles: List[SmokeParticle] = []
        
        # game state
        self.score = 0
        self.game_over = False
        self.game_won = False
        self.current_level = 1
        self.enemies_defeated = 0
        self.boss_stage = False
        self.boss = None
        self.boss_projectiles = []
        self.points_per_hit = 10  # initial value of points for hit
        
        # initialization level and stars
        self.initialize_level()
        self.initialize_stars()
        
        # Sound
        self.sound_manager = SoundManager()
        self.sound_manager.start_background_music()
        
        # game clock
        self.clock = pygame.time.Clock()
        
    def initialize_level(self):
        if self.current_level > 3:  # if we exceed level 3
            self.start_boss_stage()
            return
        
        self.enemies.clear()
        enemy_count = 5 * self.current_level
        speed_multiplier = 1 + (self.current_level - 1) * 0.5
        
        rows = min(5, (enemy_count + 4) // 5)
        cols = (enemy_count + rows - 1) // rows
        
        start_x = (self.screen_width - (cols * 100)) // 2
        start_y = 50
        
        for i in range(rows):
            for j in range(cols):
                if len(self.enemies) < enemy_count:
                    enemy = Enemy(start_x + j * 100, start_y + i * 80, 
                               self.screen_width, self.screen_height)
                    enemy.speed = int(2 * speed_multiplier)
                    self.enemies.append(enemy)

    def initialize_stars(self):
        self.stars.clear()
        for _ in range(100):
            self.stars.append(Star(
                random.random() * self.screen_width,
                random.random() * self.screen_height
            ))

    def run(self):
        running = True
        while running:
            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    self.handle_keydown(event)
                elif event.type == pygame.KEYUP:
                    self.handle_keyup(event)

            # update game state
            self.update()
            
            # Rendering
            self.render()
            
            # FPS control
            self.clock.tick(120)

        pygame.quit()

    def update(self):
        if self.game_over or self.game_won:
            return
            
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # Dash ability (shift)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.player.perform_dash()
        
        # Shooting while holding space
        if keys[pygame.K_SPACE]:
            self.handle_player_shoot()
            
        self.update_projectiles()
        self.update_enemies()
        self.update_stars()
        self.update_particles()
        
        if self.boss_stage and self.boss:
            self.update_boss()

    def render(self):
        # clearing screen
        self.screen.fill((0, 0, 20))  # dark blue background
        
        # rendering all elements
        self.render_stars()
        self.render_engine_trails()
        
        # rendering smoke particles
        for particle in self.smoke_particles:
            particle.draw(self.screen)
        
        # rendering enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # rendering projectiles
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        
        # rendering boss'ss projectiles
        for projectile in self.boss_projectiles:
            projectile.draw(self.screen)
        
        # rendering boss
        if self.boss:
            self.boss.draw(self.screen)
        
        # rendering player
        self.player.draw(self.screen)
        
        # rendering HUD and game state
        self.render_game_state()
        
        if self.dev_mode_enabled():
            self.render_debug_info()
        
        pygame.display.flip()

    def handle_keydown(self, event):
        if event.key == pygame.K_SPACE:
            self.handle_player_shoot()
        elif self.dev_mode_enabled:
            self.handle_dev_keys(event)

    def handle_keyup(self, event):
        pass 

    def handle_player_shoot(self):
        if self.player.can_shoot():
            projectile = Projectile(
                self.player.x + self.player.width // 2,
                self.player.y,
                0,
                -10 
            )
            self.projectiles.append(projectile)
            self.player.shoot()

    def handle_dev_keys(self, event):
        if event.key == pygame.K_1:
            self.start_level(1)
        elif event.key == pygame.K_2:
            self.start_level(2)
        elif event.key == pygame.K_3:
            self.start_level(3)
        elif event.key == pygame.K_4:
            self.start_boss_stage()

    def start_level(self, level):
        self.current_level = level
        self.enemies.clear()
        self.projectiles.clear()
        self.player = Player(
            self.screen_width // 2,
            self.screen_height - 50,
            30, 30,
            self.screen_width,
            self.screen_height
        )
        self.initialize_level()
        print(f"Rozpoczęto poziom {level}")

    def start_boss_stage(self):
        if not self.boss_stage:  
            self.boss_stage = True
            self.enemies.clear()
            self.projectiles.clear()
            self.boss_projectiles = []
            self.player = Player(
                self.screen_width // 2,
                self.screen_height - 50,
                30, 30,
                self.screen_width,
                self.screen_height
            )
            self.boss = Boss(self.screen_width // 2 - 50, 50)
            print("Rozpoczęto walkę z bossem")

    def update_particles(self):
        # smoke particles update
        for particle in self.smoke_particles[:]:
            particle.update()
            if particle.is_dead():
                self.smoke_particles.remove(particle)

    def add_smoke_effect(self, x, y, width, height):
        particle_count = (width * height) // 100
        base_size = min(width, height) / 4.0
        for _ in range(particle_count):
            particle_x = x + random.random() * width
            particle_y = y + random.random() * height
            particle_size = base_size * (0.5 + random.random())
            self.smoke_particles.append(SmokeParticle(particle_x, particle_y, particle_size))

    def game_over(self):
        self.game_over = True
        self.sound_manager.stop_background_music()

    def game_won(self):
        self.game_won = True
        self.sound_manager.stop_background_music()

    def update_projectiles(self):
        for projectile in self.projectiles[:]:
            projectile.update()
            
            if projectile.is_enemy:
                # check collision with player for enemy projectiles
                if projectile.intersects(self.player):
                    if self.player.take_damage(10):
                        self.game_over = True
                    self.projectiles.remove(projectile)
                    self.add_smoke_effect(
                        self.player.x, 
                        self.player.y, 
                        self.player.width, 
                        self.player.height
                    )
            else:
                # check collision with enemies for player projectiles
                hit = False
                for enemy in self.enemies[:]:
                    if projectile.intersects(enemy):
                        self.add_smoke_effect(enemy.x, enemy.y, enemy.width, enemy.height)
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        self.enemies.remove(enemy)
                        self.enemies_defeated += 1
                        self.score += self.points_per_hit  #sum of points for hit
                        hit = True
                        break

                # if projectile hit the top of the screen (did not hit)
                if not hit and projectile.y <= 0:
                    self.points_per_hit = max(3, self.points_per_hit - 1)  # decrease points for hit
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)

            # deleting projectiles that went out of the screen
            if projectile.is_out_of_bounds(self.screen_height):
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)

            # updating boss's projectiles
        if self.boss_stage and self.boss:
            for projectile in self.boss_projectiles[:]:
                projectile.update()
                
                # check collision with player
                if projectile.intersects(self.player):
                    if self.player.take_damage(33):
                        self.game_over = True
                    self.boss_projectiles.remove(projectile)
                    self.add_smoke_effect(
                        self.player.x, 
                        self.player.y, 
                        self.player.width, 
                        self.player.height
                    )
                    
                # deleting boss's projectiles that went out of the screen
                if projectile.is_out_of_bounds(self.screen_height):
                    if projectile in self.boss_projectiles:
                        self.boss_projectiles.remove(projectile)

    def update_enemies(self):
        if len(self.enemies) == 0 and not self.boss_stage:
            self.current_level += 1
            self.initialize_level()
            return

        # determine if there are few enemies left
        few_enemies_left = len(self.enemies) <= len(self.enemies) // 3

        # check if any enemy reached the edge
        change_direction = False
        for enemy in self.enemies:
            if enemy.is_at_edge():
                change_direction = True
                break

        # if any enemy reached the edge, change direction of all enemies
        if change_direction:
            for enemy in self.enemies:
                enemy.reverse_direction()
                enemy.set_target_y(enemy.y + 50)  # Lower the position

        # update positions of all enemies
        for enemy in self.enemies:
            enemy.update(few_enemies_left)  # passing information about few enemies
            
            # check collision with player
            if (enemy.x < self.player.x + self.player.width and
                enemy.x + enemy.width > self.player.x and
                enemy.y < self.player.y + self.player.height and
                enemy.y + enemy.height > self.player.y):
                self.game_over = True
                return

            # random enemy shooting
            if random.random() < 0.001:  # 0.1% chance to shoot every frame
                projectile = Projectile(
                    enemy.x + enemy.width // 2,
                    enemy.y + enemy.height,
                    0,
                    5,  # projectile speed down
                    is_enemy=True  # mark projectile as enemy
                )
                self.projectiles.append(projectile)

        # check victory conditions for level
        if len(self.enemies) == 0:
            if self.current_level >= 3:
                self.start_boss_stage()
            else:
                self.current_level += 1
                self.initialize_level()

    def update_stars(self):
        for star in self.stars:
            star.update(self.screen_height, self.screen_width)

    def render_stars(self):
        for star in self.stars:
            star.draw(self.screen)

    def render_engine_trails(self):
        for trail in self.engine_trails[:]:
            trail.update()
            trail.draw(self.screen)
            if trail.get_opacity() <= 0:
                self.engine_trails.remove(trail)

    def update_boss(self):
        if not self.boss or not self.boss_stage:
            return
        
        self.boss.update(self.player.x)
        
        # Boss attacks
        if self.boss.can_attack():
            new_projectiles = self.boss.attack()
            self.boss_projectiles.extend(new_projectiles)
            self.boss.reset_attack_cooldown()
        
        # check if boss was hit
        for projectile in self.projectiles[:]:
            if projectile.intersects(self.boss):
                self.boss.take_damage(10)
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
                self.add_smoke_effect(
                    self.boss.x + self.boss.width/2,
                    self.boss.y + self.boss.height/2,
                    20, 20
                )
        
        # check if boss was defeated
        if self.boss.is_defeated():
            self.game_won = True
            self.boss = None

    def dev_mode_enabled(self):
        return hasattr(self, '_dev_mode') and self._dev_mode

    def toggle_dev_mode(self):
        self._dev_mode = not getattr(self, '_dev_mode', False)
        print(f"Tryb developerski: {'włączony' if self._dev_mode else 'wyłączony'}")

    def render_debug_info(self):
        if not self.dev_mode_enabled():
            return
        
        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Poziom: {self.current_level}",
            f"Przeciwnicy: {len(self.enemies)}",
            f"Pociski: {len(self.projectiles)}",
            f"Pozycja gracza: ({int(self.player.x)}, {int(self.player.y)})"
        ]
        
        font = pygame.font.Font(None, 24)
        y = 10
        for text in debug_info:
            surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, y))
            y += 25

    def render_game_state(self):
        if self.game_over:
            self.render_game_over()
        elif self.game_won:
            self.render_victory()
        else:
            self.render_hud()

    def render_game_over(self):
        font = pygame.font.Font(None, 74)
        text = font.render('GAME OVER', True, (255, 0, 0))
        text_rect = text.get_rect(center=(self.screen_width/2, self.screen_height/2))
        self.screen.blit(text, text_rect)

    def render_victory(self):
        font = pygame.font.Font(None, 74)
        text = font.render('VICTORY!', True, (0, 255, 0))
        text_rect = text.get_rect(center=(self.screen_width/2, self.screen_height/2))
        self.screen.blit(text, text_rect)

    def render_hud(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        if self.boss and self.boss_stage:
            boss_health = font.render(f'Boss HP: {self.boss.health}', True, (255, 0, 0))
            self.screen.blit(boss_health, (10, 50))

        player_health = font.render(f'HP: {self.player.health}', True, (0, 255, 0))
        self.screen.blit(player_health, (10, 90))

class Enemy:
    SCALE = 4

    def __init__(self, x, y, screen_width, screen_height):
        self.x = x
        self.y = y
        self.speed = 4
        self.direction = 1  # 1 for right movement, -1 for left movement!
        self.width = 40 * self.SCALE
        self.height = 40 * self.SCALE
        self.velocity_x = 0
        self.velocity_y = 0
        self.inertia = 0.9
        self.creation_time = pygame.time.get_ticks()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.base_x = x
        self.max_deviation = 50
        self.target_y = y
        self.sprite = None
        self.load_sprite()
        self.individual_movement = False
        self.individual_target_x = x
        self.individual_target_y = y
        self.individual_timer = 0
        self.individual_interval = 120

    def load_sprite(self):
        try:
            self.sprite = pygame.image.load("Enemy.png")
            self.sprite = pygame.transform.scale(self.sprite, 
                                              (self.width, self.height))
        except pygame.error:
            print("Bąd wczytywania obrazu Enemy.png")
            self.sprite = None

    def reverse_direction(self):
        self.direction *= -1
        self.base_x = self.x  # reset base position

    def update(self, few_enemies_left):
        # Zwiększaj bezwładność z czasem
        current_time = pygame.time.get_ticks()
        self.inertia = min(0.98, self.inertia + 0.0001 * 
                          (current_time - self.creation_time) / 1000.0)

        # update base position X
        self.base_x += self.speed * self.direction

        # apply force in the direction of movement
        force = self.speed * self.direction
        
        # add random movement when there are few enemies left
        if few_enemies_left:
            force *= 1.5
            # add random movement in vertical and horizontal
            random_x = (random.random() - 0.5) * 4
            random_y = (random.random() - 0.5) * 2
            self.x += random_x
            self.y += random_y

        # update velocity and position
        self.velocity_x = self.velocity_x * self.inertia + force * (1 - self.inertia)
        self.x = self.base_x + self.velocity_x

        # smooth lowering
        if self.y < self.target_y:
            self.y = min(self.y + 0.5, self.target_y)

        # limit position to screen borders
        self.x = max(0, min(self.x, self.screen_width - self.width))
        self.y = max(50, min(self.y, self.screen_height - self.height - 100))  # added Y limit

    def draw(self, screen):
        if self.sprite:
            screen.blit(self.sprite, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (255, 0, 0), 
                           (self.x, self.y, self.width, self.height))

    def is_at_edge(self):
        return self.x <= 0 or self.x + self.width >= self.screen_width

    def set_target_y(self, new_target_y):
        self.target_y = new_target_y

    def get_position(self):
        return self.x, self.y

    def get_dimensions(self):
        return self.width, self.height

class Projectile:
    def __init__(self, x, y, speed_x, speed_y, is_enemy=False):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.width = 5
        self.height = 10
        self.is_enemy = is_enemy  # flag indicating if projectile belongs to enemy

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y

    def draw(self, screen):
        color = (255, 0, 0) if self.is_enemy else (255, 255, 0)  # red for enemies, yellow for player
        pygame.draw.rect(screen, color,
                        (self.x - self.width // 2, self.y, self.width, self.height))

    def is_out_of_bounds(self, screen_height):
        return self.y < 0 or self.y > screen_height

    def intersects(self, obj):
        return (self.x < obj.x + obj.width and
                self.x + self.width > obj.x and
                self.y < obj.y + obj.height and
                self.y + self.height > obj.y)

    def get_speed_y(self):
        return self.speed_y

    def get_position(self):
        return self.x, self.y

    def get_dimensions(self):
        return self.width, self.height


class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)
        self.speed = 0.5 + random.random()

    def update(self, screen_height, screen_width):
        self.y += self.speed
        if self.y > screen_height:
            self.y = 0
            self.x = random.random() * screen_width

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255),  # white color
                         (int(self.x), int(self.y)), self.size)


class EngineTrail:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 5
        self.opacity = 255  # full opacity

    def update(self):
        self.y += 2
        self.size += 1
        self.opacity = max(0, self.opacity - 13)  # decrease opacity

    def draw(self, screen):
        if self.opacity > 0:
            surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(surface, (0, 255, 255, self.opacity),  # cyan color with opacity
                             (self.size // 2, self.size // 2), self.size // 2)
            screen.blit(surface, (self.x - self.size // 2, self.y - self.size // 2))

    def get_opacity(self):
        return self.opacity


class BossProjectile(Projectile):
    WIDTH = 15
    HEIGHT = 30
    TRAIL_LENGTH = 10

    def __init__(self, x, y, speed_x, speed_y):
        super().__init__(x, y, speed_x, speed_y)
        self.trail = []
        self.width = self.WIDTH
        self.height = self.HEIGHT

    def update(self):
        super().update()
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.TRAIL_LENGTH:
            self.trail.pop(0)

    def draw(self, screen):
        # drawing trail
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(255 * i / len(self.trail))
            surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(surface, (255, 165, 0, alpha),  # orange color with opacity
                           (0, 0, self.width, self.height))
            screen.blit(surface, (trail_x - self.width//2, trail_y - self.height//2))

        # drawing projectile
        pygame.draw.rect(screen, (255, 165, 0),  # orange color
                        (self.x - self.width//2, self.y - self.height//2, 
                         self.width, self.height))

    def is_out_of_bounds(self, screen_height):
        return self.y - self.height//2 - self.TRAIL_LENGTH * self.height > screen_height


class SmokeParticle:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.lifespan = 30 + int(random.random() * 30)
        self.color = (200, 200, 200, 255)  # smoke color with full opacity

    def update(self):
        self.lifespan -= 1
        self.size += 0.2
        self.x += (random.random() - 0.5) * 2
        self.y += (random.random() - 0.5) * 2
        alpha = int(255 * (self.lifespan / 60.0))
        self.color = (200, 200, 200, alpha)

    def draw(self, screen):
        surface = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
        pygame.draw.circle(surface, self.color,
                         (int(self.size/2), int(self.size/2)), int(self.size/2))
        screen.blit(surface, (int(self.x - self.size/2), int(self.y - self.size/2)))

    def is_dead(self):
        return self.lifespan <= 0

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 150
        self.height = 150
        self.health = 1000
        self.attack_cooldown = 0
        self.speed = 2  # decreased speed
        self.attack_patterns = ['normal', 'spread', 'circle']
        self.current_pattern = 0
        self.pattern_change_timer = 300
        self.target_x = x
        self.target_y = y
        self.move_timer = 0
        self.move_interval = 180  # longer movement interval
        self.max_offset = 200  # larger movement range

    def update(self, player_x):
        # update movement timer
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            # select new random target in a larger range
            self.target_x = max(0, min(800 - self.width, 
                              self.x + random.randint(-self.max_offset, self.max_offset)))
            self.target_y = max(50, min(300, 
                              self.y + random.randint(-100, 100)))  # larger range in vertical
            
        # smooth movement towards target
        dx = (self.target_x - self.x) * 0.02  # slower movement
        dy = (self.target_y - self.y) * 0.02
        
        self.x += dx
        self.y += dy
        
        # remaining boss logic
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.pattern_change_timer -= 1
        if self.pattern_change_timer <= 0:
            self.current_pattern = (self.current_pattern + 1) % len(self.attack_patterns)
            self.pattern_change_timer = 300

    def attack(self):
        pattern = self.attack_patterns[self.current_pattern]
        projectiles = []
        
        if pattern == 'normal':
            projectiles.append(BossProjectile(
                self.x + self.width/2,
                self.y + self.height,
                0, 5
            ))
        elif pattern == 'spread':
            for i in range(-2, 3):
                projectiles.append(BossProjectile(
                    self.x + self.width/2,
                    self.y + self.height,
                    i * 2, 5
                ))
        elif pattern == 'circle':
            for i in range(8):
                angle = i * math.pi / 4
                projectiles.append(BossProjectile(
                    self.x + self.width/2,
                    self.y + self.height,
                    math.cos(angle) * 5,
                    math.sin(angle) * 5
                ))
        
        return projectiles

    def can_attack(self):
        return self.attack_cooldown == 0

    def reset_attack_cooldown(self):
        self.attack_cooldown = 60

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)

    def is_defeated(self):
        return self.health <= 0

    def draw(self, screen):
        # Rysowanie bossa
        pygame.draw.rect(screen, (255, 0, 0),
                        (self.x, self.y, self.width, self.height))
        # Pasek życia
        health_width = int(self.width * self.health / 1000)
        pygame.draw.rect(screen, (0, 255, 0),
                        (self.x, self.y - 10, health_width, 5))

    def get_position(self):
        return self.x, self.y

    def get_dimensions(self):
        return self.width, self.height

class SoundManager:
    def __init__(self):
        self.background_sounds = []
        self.current_sound_index = 0
        self.volume = 0.2  # 20% volume

        sound_files = [
            "space-sound-hi-109577.wav",
            "space-sound-hi-low-109574.wav",
            "space-sound-mid-109575.wav"
        ]

        # initialize mixer
        pygame.mixer.init()
        
        # loading sound files
        for file in sound_files:
            try:
                sound = pygame.mixer.Sound(file)
                sound.set_volume(self.volume)
                self.background_sounds.append(sound)
            except pygame.error as e:
                print(f"Nie można załadować pliku dźwiękowego: {file}")
                print(f"Błąd: {e}")

    def start_background_music(self):
        if self.background_sounds:
            current_sound = self.background_sounds[self.current_sound_index]
            current_sound.play()
            # setting callback to next track
            pygame.mixer.music.set_endevent(pygame.USEREVENT)

    def next_background_track(self):
        self.current_sound_index = (self.current_sound_index + 1) % len(self.background_sounds)
        self.start_background_music()

    def stop_background_music(self):
        for sound in self.background_sounds:
            sound.stop()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.background_sounds:
            sound.set_volume(self.volume)


class SoundPlayer:
    def __init__(self, filename: str):
        self.sound = None
        try:
            if os.path.exists(filename):
                self.sound = pygame.mixer.Sound(filename)
                print(f"Dźwięk załadowany pomyślnie: {filename}")
            else:
                print(f"Plik dźwiękowy nie istnieje: {filename}")
        except pygame.error as e:
            print(f"Błąd podczas ładowania dźwięku: {e}")

    def play(self):
        if self.sound:
            self.sound.play()
            print("Rozpoczęto odtwarzanie dźwięku")
        else:
            print("Nie można odtworzyć dźwięku: sound jest None")

    def stop(self):
        if self.sound:
            self.sound.stop()
            print("Zatrzymano odtwarzanie dźwięku")

class Player:
    VERTICAL_MOVEMENT_LIMIT = 0.25
    MAX_SPEED = 8.0
    DASH_SPEED = 20.0
    DASH_COOLDOWN = 1000
    DASH_DURATION = 10
    SHOT_COOLDOWN = 250  # increased shot cooldown (before was 100)

    def __init__(self, x, y, width, height, screen_width, screen_height):
        self.x = x
        self.y = y
        self.width = width * 2
        self.height = height * 2
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.velocity_x = 0
        self.velocity_y = 0
        self.acceleration = 0.8
        self.deceleration = 0.9
        self.last_dash_time = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.last_shot_time = 0
        self.health = 100
        self.dash_direction_x = 0
        self.dash_direction_y = 0

    def perform_dash(self):
        current_time = pygame.time.get_ticks()
        if not self.is_dashing and current_time - self.last_dash_time >= self.DASH_COOLDOWN:
            keys = pygame.key.get_pressed()
            
            # set dash direction based on pressed keys
            self.dash_direction_x = 0
            self.dash_direction_y = 0
            
            if keys[pygame.K_LEFT]: self.dash_direction_x = -1
            if keys[pygame.K_RIGHT]: self.dash_direction_x = 1
            if keys[pygame.K_UP]: self.dash_direction_y = -1
            if keys[pygame.K_DOWN]: self.dash_direction_y = 1
            
            # perform dash only if any direction key is pressed
            if self.dash_direction_x != 0 or self.dash_direction_y != 0:
                self.is_dashing = True
                self.dash_timer = self.DASH_DURATION
                self.last_dash_time = current_time

    def update(self, keys):
        if self.is_dashing:
            # update position during dash
            self.x += self.dash_direction_x * self.DASH_SPEED
            self.y += self.dash_direction_y * self.DASH_SPEED
            
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.velocity_x = 0
                self.velocity_y = 0
        else:
            # normal movement update
            if keys[pygame.K_LEFT]:
                self.velocity_x -= self.acceleration
            if keys[pygame.K_RIGHT]:
                self.velocity_x += self.acceleration
            if keys[pygame.K_UP]:
                self.velocity_y -= self.acceleration
            if keys[pygame.K_DOWN]:
                self.velocity_y += self.acceleration

            # applying air resistance
            self.velocity_x *= self.deceleration
            self.velocity_y *= self.deceleration

            # limiting max speed
            speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
            if speed > self.MAX_SPEED:
                self.velocity_x = (self.velocity_x / speed) * self.MAX_SPEED
                self.velocity_y = (self.velocity_y / speed) * self.MAX_SPEED

            # update position
            self.x += self.velocity_x
            self.y += self.velocity_y

        # limiting position to screen boundaries
        self.x = max(0, min(self.x, self.screen_width - self.width))
        min_y = int(self.screen_height * (1 - self.VERTICAL_MOVEMENT_LIMIT))
        self.y = max(min_y, min(self.y, self.screen_height - self.height))

    def draw(self, screen):
        # drawing triangular ship
        points = [
            (self.x + self.width // 2, self.y),  # ship's nose
            (self.x, self.y + self.height),      # left corner
            (self.x + self.width, self.y + self.height)  # right corner
        ]
        pygame.draw.polygon(screen, (0, 255, 255), points)  # CYAN color

    def can_shoot(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_shot_time >= self.SHOT_COOLDOWN

    def shoot(self):
        self.last_shot_time = pygame.time.get_ticks()

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def get_position(self):
        return self.x, self.y

    def get_dimensions(self):
        return self.width, self.height

if __name__ == "__main__":
    game = SpaceInvadersGame()
    game.run()