#!/usr/bin/env python3
import os
import time
import json
import pygame
import random
import math
import numpy as np

# Initialize pygame
pygame.init()
# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 6
GRAVITY = 0.5
JUMP_STRENGTH = 15
MAX_LEVEL = 3
DOUBLE_JUMP_STRENGTH = 13  # Slightly lower strength for double jump

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Speedrun Challenge")
clock = pygame.time.Clock()

# Font setup
font = pygame.font.SysFont("Arial", 24)
title_font = pygame.font.SysFont("Arial", 48, bold=True)

# Background stars
stars = []
for i in range(50):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(1, 3)
    brightness = random.randint(100, 255)
    stars.append([x, y, size, brightness])


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Create player animation frames (simple colored rectangles for now)
        self.frames = []
        base_image = pygame.Surface((30, 50), pygame.SRCALPHA)
        pygame.draw.rect(base_image, BLUE, (0, 0, 30, 50))
        pygame.draw.rect(base_image, CYAN, (5, 5, 20, 10))  # Eyes
        self.frames.append(base_image)
        
        run_image = pygame.Surface((30, 50), pygame.SRCALPHA)
        pygame.draw.rect(run_image, BLUE, (0, 0, 30, 50))
        pygame.draw.rect(run_image, CYAN, (5, 5, 20, 10))  # Eyes
        pygame.draw.rect(run_image, WHITE, (15, 45, 10, 5))  # Feet animation
        self.frames.append(run_image)
        
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.is_jumping = False
        self.can_double_jump = True
        self.facing_right = True
        self.frame_index = 0
        self.animation_timer = 0
        
        # Trail effect
        self.trail = []
        self.trail_timer = 0
        
    def update(self, platforms):
        # Trail effect
        self.trail_timer += 1
        if self.trail_timer > 3:  # Add trail position every few frames
            self.trail_timer = 0
            # Only add trail when moving
            if abs(self.vel_x) > 0 or abs(self.vel_y) > 0:
                self.trail.append([self.rect.centerx, self.rect.centery, 15])  # x, y, lifetime
        
        # Update trail positions
        for i, trail in enumerate(self.trail):
            trail[2] -= 1  # Decrease lifetime
        
        # Remove dead trails
        self.trail = [trail for trail in self.trail if trail[2] > 0]
        
        # Animation
        self.animation_timer += 1
        if self.animation_timer > 10:  # Change frame every 10 ticks
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            if self.vel_x != 0:  # Only animate when moving
                self.image = self.frames[self.frame_index]
            else:
                self.image = self.frames[0]  # Idle frame
                
        # Flip image based on direction
        if self.vel_x < 0 and self.facing_right:
            self.facing_right = False
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.vel_x > 0 and not self.facing_right:
            self.facing_right = True
            self.image = pygame.transform.flip(self.image, True, False)
            
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Move horizontally
        self.rect.x += self.vel_x
        
        # Check for collisions with platforms horizontally
        platform_hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in platform_hits:
            if self.vel_x > 0:  # Moving right
                self.rect.right = platform.rect.left
            elif self.vel_x < 0:  # Moving left
                self.rect.left = platform.rect.right
        
        # Move vertically
        self.rect.y += self.vel_y
        
        # Check for collisions with platforms vertically
        self.on_ground = False
        platform_hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in platform_hits:
            if self.vel_y > 0:  # Falling
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
                self.is_jumping = False
                self.can_double_jump = True
            elif self.vel_y < 0:  # Jumping
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        
        # Boundary check
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
    
    def jump(self):
        if self.on_ground and not self.is_jumping:
            self.vel_y = -JUMP_STRENGTH
            self.is_jumping = True
            self.on_ground = False
        elif not self.on_ground and self.can_double_jump:
            self.vel_y = -DOUBLE_JUMP_STRENGTH  # Slightly weaker double jump
            self.can_double_jump = False
    
    def draw_trail(self, surface):
        for x, y, lifetime in self.trail:
            # Fade based on lifetime
            alpha = min(255, lifetime * 17)  
            # Draw trail particle
            pygame.draw.circle(surface, (100, 200, 255, alpha), (x, y), max(1, lifetime//5))


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=GRAY):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        
        # Add a highlight on top
        pygame.draw.rect(self.image, (min(color[0] + 30, 255), 
                                      min(color[1] + 30, 255), 
                                      min(color[2] + 30, 255)), 
                        (0, 0, width, 3))
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class FinishLine(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        
        # Draw a flag
        pygame.draw.rect(self.image, GREEN, (0, 0, 5, 60))  # Flagpole
        pygame.draw.polygon(self.image, YELLOW, [(5, 5), (40, 15), (5, 25)])  # Flag
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Arrow animation for visibility
        self.arrow_offset = 0
        self.arrow_dir = 1
    
    def update(self):
        # Animate arrow
        self.arrow_offset += 0.5 * self.arrow_dir
        if self.arrow_offset > 10 or self.arrow_offset < 0:
            self.arrow_dir *= -1
    
    def draw_arrow(self, surface):
        # Draw arrow pointing at finish
        arrow_y = self.rect.y - 30 - self.arrow_offset
        points = [
            (self.rect.centerx, arrow_y), 
            (self.rect.centerx - 10, arrow_y - 10),
            (self.rect.centerx + 10, arrow_y - 10)
        ]
        pygame.draw.polygon(surface, YELLOW, points)


class Hazard(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw spikes
        spike_width = 10
        num_spikes = width // spike_width
        for i in range(num_spikes):
            pygame.draw.polygon(self.image, RED, 
                             [(i * spike_width, height), 
                              (i * spike_width + spike_width//2, 0), 
                              (i * spike_width + spike_width, height)])
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (7, 7), 7)
        pygame.draw.circle(self.image, ORANGE, (7, 7), 5)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Game:
    def __init__(self):
        # Create groups for sprites
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()
        self.finish_group = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        
        # Create player
        self.player = Player(50, 300)
        self.all_sprites.add(self.player)
        
        # Game state
        self.current_level = 1
        self.collected_coins = 0
        self.total_coins = 0
        self.show_main_menu = True
        self.level_complete = False
        
        # Timer variables
        self.running = False
        self.start_time = 0
        self.current_time = 0
        self.best_times = self.load_best_times()
    
    def reset_level(self):
        # Clear all sprites
        self.all_sprites.empty()
        self.platforms.empty()
        self.hazards.empty()
        self.finish_group.empty()
        self.coins.empty()
        
        # Reset player
        self.player = Player(50, 300)
        self.all_sprites.add(self.player)
        
        # Reset coins collected
        self.collected_coins = 0
        self.total_coins = 0
        
        # Create level
        self.create_level(self.current_level)
        
        # Reset timer
        self.start_timer()
    
    def create_level(self, level_num):
        # Create finish line
        if level_num == 1:
            self.finish = FinishLine(700, 500)
        elif level_num == 2:
            self.finish = FinishLine(700, 300)
        else:
            self.finish = FinishLine(700, 90)  # Moved finish line above the platform at y=150
        
        self.all_sprites.add(self.finish)
        self.finish_group.add(self.finish)
        
        # Create the ground for all levels
        ground = Platform(0, 550, SCREEN_WIDTH, 50, GRAY)
        self.all_sprites.add(ground)
        self.platforms.add(ground)
        
        if level_num == 1:
            # Level 1 - Easy introduction
            platforms = [
                (100, 450, 200, 20),
                (350, 450, 150, 20),
                (550, 500, 150, 20),  # Platform leading to finish
                (200, 350, 150, 20),
                (400, 250, 150, 20),
                (250, 150, 100, 20),
            ]
            
            hazards = [
                (150, 500, 50, 20),
                (450, 400, 50, 20),
                (300, 200, 50, 20),
            ]
            
            coins_pos = [
                (150, 420),
                (400, 420),
                (600, 470),
                (250, 320),
                (450, 220),
            ]
            
        elif level_num == 2:
            # Level 2 - Medium difficulty
            platforms = [
                (100, 500, 100, 20),
                (250, 450, 100, 20),
                (400, 400, 100, 20),
                (550, 350, 100, 20),
                (700, 350, 50, 20),
                (150, 300, 80, 20),
                (300, 250, 80, 20),
                (450, 200, 80, 20),
                (600, 150, 80, 20),
            ]
            
            hazards = [
                (200, 500, 50, 20),
                (350, 450, 50, 20),
                (500, 400, 50, 20),
                (650, 300, 50, 20),
                (250, 200, 50, 20),
                (400, 150, 50, 20),
            ]
            
            coins_pos = [
                (100, 470),
                (250, 420),
                (400, 370),
                (550, 320),
                (150, 270),
                (300, 220),
                (450, 170),
                (600, 120),
            ]
            
        else:  # Level 3
            # Level 3 - Hard challenge but actually possible to complete
            platforms = [
                (100, 500, 70, 20),
                (250, 470, 70, 20),
                (170, 400, 70, 20),
                (300, 350, 70, 20),
                (400, 300, 70, 20),
                (300, 250, 70, 20),
                (500, 200, 70, 20),
                (650, 200, 100, 20),  # Extended platform leading to finish
                (400, 150, 70, 20),
                (550, 100, 70, 20),
                (700, 150, 70, 20),  # Platform at finish
            ]
            
            hazards = [
                (180, 530, 60, 20),
                (320, 500, 60, 20),
                (240, 400, 50, 20),
                (350, 300, 50, 20),
                (400, 250, 60, 20),
                (450, 150, 50, 20),  # Moved away from critical path
                (600, 100, 50, 20),  # Moved away from critical path
            ]
            
            coins_pos = [
                (100, 470),
                (250, 440),
                (170, 370),
                (300, 320),
                (400, 270),
                (300, 220),
                (500, 170),
                (650, 170),
                (400, 120),
                (550, 70),
            ]
        
        # Create platforms
        for x, y, w, h in platforms:
            platform = Platform(x, y, w, h)
            self.all_sprites.add(platform)
            self.platforms.add(platform)
        
        # Create hazards
        for x, y, w, h in hazards:
            hazard = Hazard(x, y, w, h)
            self.all_sprites.add(hazard)
            self.hazards.add(hazard)
        
        # Create coins
        for x, y in coins_pos:
            coin = Coin(x, y)
            self.all_sprites.add(coin)
            self.coins.add(coin)
            self.total_coins += 1
    
    def load_best_times(self):
        best_times = {}
        try:
            if os.path.exists("best_times.json"):
                with open("best_times.json", "r") as f:
                    best_times = json.load(f)
        except Exception:
            pass
        
        # Initialize any missing levels
        for level in range(1, MAX_LEVEL + 1):
            level_key = f"level_{level}"
            if level_key not in best_times:
                best_times[level_key] = float('inf')
        
        return best_times
    
    def save_best_times(self):
        try:
            with open("best_times.json", "w") as f:
                json.dump(self.best_times, f)
        except Exception as e:
            print(f"Error saving best times: {e}")
    
    def start_timer(self):
        self.running = True
        self.start_time = time.time()
    
    def stop_timer(self):
        self.running = False
        self.current_time = time.time() - self.start_time
        level_key = f"level_{self.current_level}"
        if self.current_time < self.best_times[level_key]:
            self.best_times[level_key] = self.current_time
            self.save_best_times()
            return True
        return False
    
    def format_time(self, seconds):
        if seconds == float('inf'):
            return "N/A"
        return f"{seconds:.2f}s"
    
    def draw_background(self):
        # Draw space background
        screen.fill((10, 10, 40))  # Dark blue
        
        # Draw stars
        for star in stars:
            color = (star[3], star[3], star[3])  # White with varying brightness
            pygame.draw.circle(screen, color, (star[0], star[1]), star[2])
    
    def draw_main_menu(self):
        self.draw_background()
        
        # Draw title
        title = title_font.render("SPEEDRUN CHALLENGE", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Draw level buttons
        for level in range(1, MAX_LEVEL + 1):
            level_key = f"level_{level}"
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 200 + 60 * level, 200, 50)
            pygame.draw.rect(screen, BLUE, button_rect)
            pygame.draw.rect(screen, WHITE, button_rect, 2)  # Border
            
            level_text = font.render(f"Level {level}", True, WHITE)
            screen.blit(level_text, (button_rect.centerx - level_text.get_width()//2, 
                                     button_rect.centery - level_text.get_height()//2))
            
            # Show best time for level
            time_text = font.render(f"Best: {self.format_time(self.best_times[level_key])}", True, YELLOW)
            screen.blit(time_text, (button_rect.centerx - time_text.get_width()//2, 
                                    button_rect.bottom + 10))
        
        # Draw instructions
        instructions = font.render("Click a level to begin!", True, WHITE)
        screen.blit(instructions, (SCREEN_WIDTH//2 - instructions.get_width()//2, 500))
        
        # Calculate and display total best time (sum of all levels)
        total_best_time = sum(self.best_times.get(f"level_{level}", float('inf')) for level in range(1, MAX_LEVEL + 1))
        total_time_text = font.render(f"Total Best Time: {self.format_time(total_best_time)}", True, GREEN)
        screen.blit(total_time_text, (SCREEN_WIDTH//2 - total_time_text.get_width()//2, 540))
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(overlay, (0, 0))
        
        # Draw completion message
        complete_text = title_font.render(f"LEVEL {self.current_level} COMPLETE!", True, YELLOW)
        screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, 150))
        
        # Show time
        time_text = font.render(f"Time: {self.format_time(self.current_time)}", True, WHITE)
        screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, 220))
        
        # Show coins collected
        coins_text = font.render(f"Coins: {self.collected_coins}/{self.total_coins}", True, YELLOW)
        screen.blit(coins_text, (SCREEN_WIDTH//2 - coins_text.get_width()//2, 260))
        
        # Draw buttons
        if self.current_level < MAX_LEVEL:
            next_rect = pygame.Rect(SCREEN_WIDTH//2 - 210, 350, 200, 50)
            pygame.draw.rect(screen, GREEN, next_rect)
            pygame.draw.rect(screen, WHITE, next_rect, 2)
            next_text = font.render("Next Level", True, WHITE)
            screen.blit(next_text, (next_rect.centerx - next_text.get_width()//2, 
                                   next_rect.centery - next_text.get_height()//2))
        
        retry_rect = pygame.Rect(SCREEN_WIDTH//2 + 10, 350, 200, 50)
        pygame.draw.rect(screen, BLUE, retry_rect)
        pygame.draw.rect(screen, WHITE, retry_rect, 2)
        retry_text = font.render("Retry Level", True, WHITE)
        screen.blit(retry_text, (retry_rect.centerx - retry_text.get_width()//2, 
                               retry_rect.centery - retry_text.get_height()//2))
        
        menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 420, 200, 50)
        pygame.draw.rect(screen, GRAY, menu_rect)
        pygame.draw.rect(screen, WHITE, menu_rect, 2)
        menu_text = font.render("Main Menu", True, WHITE)
        screen.blit(menu_text, (menu_rect.centerx - menu_text.get_width()//2, 
                              menu_rect.centery - menu_text.get_height()//2))
        
        return (next_rect if self.current_level < MAX_LEVEL else None, retry_rect, menu_rect)
    
    def handle_level_complete_input(self, pos, next_rect, retry_rect, menu_rect):
        if next_rect and next_rect.collidepoint(pos):
            self.current_level += 1
            self.level_complete = False
            self.reset_level()
        elif retry_rect.collidepoint(pos):
            self.level_complete = False
            self.reset_level()
        elif menu_rect.collidepoint(pos):
            self.show_main_menu = True
            self.level_complete = False
    
    def run(self):
        # Game variables
        game_active = False
        
        # Main game loop
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if game_active:
                            self.show_main_menu = True
                            game_active = False
                        else:
                            running = False
                    
                    if event.key == pygame.K_r and game_active and not self.level_complete:
                        self.reset_level()
                    
                    if game_active and not self.level_complete:
                        if event.key == pygame.K_SPACE:
                            self.player.jump()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        pos = pygame.mouse.get_pos()
                        
                        # Handle main menu clicks
                        if self.show_main_menu:
                            for level in range(1, MAX_LEVEL + 1):
                                button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 200 + 60 * level, 200, 50)
                                if button_rect.collidepoint(pos):
                                    self.current_level = level
                                    self.show_main_menu = False
                                    game_active = True
                                    self.reset_level()
                        
                        # Handle level complete screen clicks
                        elif self.level_complete:
                            next_rect, retry_rect, menu_rect = self.draw_level_complete()
                            self.handle_level_complete_input(pos, next_rect, retry_rect, menu_rect)
            
            # Draw background
            self.draw_background()
            
            # Main menu
            if self.show_main_menu:
                self.draw_main_menu()
            # Game play
            elif game_active and not self.level_complete:
                # Get the pressed keys
                keys = pygame.key.get_pressed()
                self.player.vel_x = 0
                if keys[pygame.K_LEFT]:
                    self.player.vel_x = -PLAYER_SPEED
                if keys[pygame.K_RIGHT]:
                    self.player.vel_x = PLAYER_SPEED
                
                # Update player
                self.player.update(self.platforms)
                
                # Check for coin collection
                coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
                for coin in coin_hits:
                    self.collected_coins += 1
                
                # Check for finish
                if pygame.sprite.spritecollide(self.player, self.finish_group, False):
                    game_active = True
                    self.level_complete = True
                    new_record = self.stop_timer()
                
                # Check for hazards
                if pygame.sprite.spritecollide(self.player, self.hazards, False):
                    self.reset_level()
                
                # Check for falling off the screen
                if self.player.rect.top > SCREEN_HEIGHT:
                    self.reset_level()
                
                # Update timer if the game is running
                if self.running:
                    self.current_time = time.time() - self.start_time
                
                # Update finish line animation
                self.finish.update()
                
                # Draw game elements
                self.all_sprites.draw(screen)
                
                # Draw player trail behind player
                self.player.draw_trail(screen)
                
                # Draw finish line arrow
                self.finish.draw_arrow(screen)
                
                # Draw UI
                # Timer
                timer_text = font.render(f"Time: {self.format_time(self.current_time)}", True, WHITE)
                screen.blit(timer_text, (10, 10))
                
                # Best time
                level_key = f"level_{self.current_level}"
                best_time_text = font.render(f"Best: {self.format_time(self.best_times[level_key])}", True, YELLOW)
                screen.blit(best_time_text, (10, 40))
                
                # Coins
                coins_text = font.render(f"Coins: {self.collected_coins}/{self.total_coins}", True, YELLOW)
                screen.blit(coins_text, (10, 70))
                
                # Level indicator
                level_text = font.render(f"Level {self.current_level}", True, WHITE)
                screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 10, 10))
                
                # Controls reminder
                controls_text = font.render("Arrows: Move | Space: Jump (x2) | R: Reset | ESC: Menu", True, WHITE)
                screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, SCREEN_HEIGHT - 30))
            
            # Level complete screen
            elif self.level_complete:
                # First draw the game behind the overlay
                self.all_sprites.draw(screen)
                # Then draw the level complete screen
                self.draw_level_complete()
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(FPS)
        
        pygame.quit()


# Create assets directory if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")


if __name__ == "__main__":
    game = Game()
    game.run() 