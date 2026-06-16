import pygame as pg
import sys
import math 
import random
import settings
from enum import Enum
import time

# Инициализация Pygame
pg.init()

# Настройки экрана
CELL_SIZE = 256
CHUNK_SIZE = 64
map_test = {}
sprites = {}

# Создаем полноэкранное окно
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pg.display.set_caption("Game")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Игрок
pl_si = 64
try:
    pl_sprite = pg.image.load("unknown_game_DL/sprite/player.png")
    pl_sprite = pg.transform.scale(pl_sprite, (pl_si, pl_si))
except:
    pl_sprite = pg.Surface((pl_si, pl_si))
    pl_sprite.fill(RED)

player_size = pg.Rect(5 * pl_si, 5 * pl_si, pl_si, pl_si)
speed = 500

# Камера
camera_x0, camera_y0 = 0, 0

class BiomesType(Enum):
    SEA = 0
    LAND = 1
    SAND = 2
    SEA_SHORE = 3
    WOODS = 4

class Biomes:
    def __init__(self, screen, pg):
        self.screen = screen
        self.pg = pg
        self.matrix = self.create_start_matrix()
        self.sprites = {}
        self.ground_sprites = []
        self.tree_positions = []
        self.load_all_sprites()
        
    def load_all_sprites(self):
        """Загрузка всех спрайтов"""
        sprite_files = {
            BiomesType.SEA_SHORE: "unknown_game_DL/sprite/1000091955.jpg",
            BiomesType.SEA: "unknown_game_DL/sprite/waterwaves.jpg" ,
            BiomesType.SAND: "unknown_game_DL/sprite/1000091956.jpg",
            BiomesType.WOODS: "unknown_game_DL/sprite/tree21.png"
        }
            
        for biome, path in sprite_files.items():
            try:
                sprite = pg.image.load(path)
                sprite = pg.transform.scale(sprite, (CELL_SIZE, CELL_SIZE))
                self.sprites[biome] = sprite
                print(f"Загружен спрайт для {biome}")
            except:
                # Если спрайта нет, создаем цветной прямоугольник
                print(f"Спрайт для {biome} не найден, использую цвет")
                self.sprites[biome] = None
        ground_textures = [
            "unknown_game_DL/sprite/grass1.jpg",
            "unknown_game_DL/sprite/grass2.jpg",
            "unknown_game_DL/sprite/grass3.jpg"
        ]
        for path in ground_textures:
            try:
                sprite = pg.image.load(path)
                sprite = pg.transform.scale(sprite, (CELL_SIZE, CELL_SIZE))
                self.ground_sprites.append(sprite)
                print(f"Загружен спрайт травы: {path}")
            except:
                # Если нет картинок, создаем вариации цветов
                surf = pg.Surface((CELL_SIZE, CELL_SIZE))
                # Разные оттенки зеленого
                green_variations = [
                    (34, 139, 34),   # Обычный зеленый
                    (40, 150, 40),   # Светлее
                    (28, 128, 28),   # Темнее
                    (45, 155, 45)    # Ярче
                ]
                for i, color in enumerate(green_variations):
                    surf.fill(color)
                    self.ground_sprites.append(surf.copy())
                print(f"Созданы текстуры травы (заглушки)")
                break
        try:
            self.tree_sprite = pg.image.load("unknown_game_DL/sprite/tree21.png")
            self.tree_sprite = pg.transform.scale(self.tree_sprite, (CELL_SIZE , CELL_SIZE ))
        except:
            # Создаем простой спрайт если нет файла
            self.tree_sprite = pg.Surface((CELL_SIZE , CELL_SIZE ), pg.SRCALPHA)
            pg.draw.circle(self.tree_sprite, (34, 139, 34), (CELL_SIZE // 4, CELL_SIZE // 4), CELL_SIZE // 4)
        

    def get_biome_sprite(self, biome, x=None, y=None):
        
        if biome == BiomesType.LAND:
            if self.ground_sprites:
                # Используем позицию для детерминированного выбора
                if x is not None and y is not None:
                    # Один и тот же тайл всегда будет одинаковым
                    index = (x * 7 + y * 13) % len(self.ground_sprites)
                    return self.ground_sprites[index]
                else:
                    # Случайный выбор
                    return random.choice(self.ground_sprites)
            else:
                # Если нет спрайтов, возвращаем цвет
                color = self.get_color(biome)
                surf = pg.Surface((CELL_SIZE, CELL_SIZE))
                surf.fill(color)
                return surf
        
        # Для остальных биомов - обычные спрайты
        sprite = self.sprites.get(biome)
        if sprite is not None:
            return sprite
        
        color = self.get_color(biome)
        surf = pg.Surface((CELL_SIZE, CELL_SIZE))
        surf.fill(color)
    
    def main_render_biomes(self):
        start = time.time()
        self.set_layout_lands_and_sea()  # Шаг 1: Создаем континенты
        self.set_layout_beaches()        # Шаг 2: Добавляем пляжи (ТОЛЬКО у воды)
        self.generate_trees()         # Шаг 3: Добавляем леса
        print(f'Render Time is {time.time() - start:.2f}s')
        
        # Статистика после генерации
        self.print_stats()

    def print_stats(self):
        """Выводит статистику биомов"""
        stats = {
            BiomesType.SEA: 0,
            BiomesType.LAND: 0,
            BiomesType.SAND: 0,
            BiomesType.SEA_SHORE: 0,
            BiomesType.WOODS: 0
        }

        for row in self.matrix:
            for cell in row:
                stats[cell] += 1
        
        total = sum(stats.values())
        print(f"\n=== СТАТИСТИКА БИОМОВ ===")
        print(f"Море (SEA): {stats[BiomesType.SEA]} ({stats[BiomesType.SEA]/total*100:.1f}%)")
        print(f"Земля (LAND): {stats[BiomesType.LAND]} ({stats[BiomesType.LAND]/total*100:.1f}%)")
        print(f"Песок (SAND): {stats[BiomesType.SAND]} ({stats[BiomesType.SAND]/total*100:.1f}%)")
        print(f"Лес (WOODS): {stats[BiomesType.WOODS]} ({stats[BiomesType.WOODS]/total*100:.1f}%)")
        print(f"Мелководье: {stats[BiomesType.SEA_SHORE]} ({stats[BiomesType.SEA_SHORE]/total*100:.1f}%)")

    # -------------------- LAND & SEA --------------------
    def set_layout_lands_and_sea(self):
        """Создание континентов (только море и земля)"""
        for _ in range(settings.COUNTS_ALGORITHMS):
            # Море превращается в землю, если рядом много земли
            self.next_generation(BiomesType.SEA, BiomesType.LAND, [5,6,7,8])
            # Земля превращается в море, если рядом много моря
            self.next_generation(BiomesType.LAND, BiomesType.SEA, [4,6,7,8])
    
    # -------------------- GENERIC --------------------
    def count_neighbors(self, x, y, biome_type):
        """Подсчет соседей (включая диагональные)"""
        count = 0
        rows, cols = len(self.matrix), len(self.matrix[0])
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    if self.matrix[nx][ny] == biome_type:
                        count += 1
        return count

    def next_generation(self, target_biome, new_biome, rules):
        """Один шаг клеточного автомата"""
        rows, cols = len(self.matrix), len(self.matrix[0])
        new_matrix = [row[:] for row in self.matrix]
        
        for x in range(rows):
            for y in range(cols):
                if self.matrix[x][y] == target_biome:
                    neighbors = self.count_neighbors(x, y, new_biome)
                    if neighbors in rules:
                        new_matrix[x][y] = new_biome
        
        self.matrix = new_matrix

    # -------------------- BEACHES (ПЛЯЖИ) --------------------
    def set_layout_beaches(self):
        """Создание пляжей ТОЛЬКО на границе земли и моря"""
        rows, cols = len(self.matrix), len(self.matrix[0])
        
        # Сначала создаем мелководье
        for x in range(rows):
            for y in range(cols):
                if self.matrix[x][y] == BiomesType.SEA:
                    if self.count_neighbors(x, y, BiomesType.LAND) >= 1:
                        self.matrix[x][y] = BiomesType.SEA_SHORE
        
        # Затем создаем песок на земле у моря
        for x in range(rows):
            for y in range(cols):
                if self.matrix[x][y] == BiomesType.LAND:
                    if self.count_neighbors(x, y, BiomesType.SEA) >= 1 or \
                       self.count_neighbors(x, y, BiomesType.SEA_SHORE) >= 1:
                        self.matrix[x][y] = BiomesType.SAND

    # -------------------- WOODS --------------------
    def generate_trees(self):
        """Генерация деревьев на земле"""
        rows, cols = len(self.matrix), len(self.matrix[0])
        for x in range(rows):
            for y in range(cols):
                if self.matrix[y][x] == BiomesType.LAND:
                    if random.randint(1, 3) == 1:  # 33% шанс дерева
                        self.tree_positions.append((x, y))
    
    def set_layout_woods(self):
        """Создание лесов на земле (не на песке)"""
        rows, cols = len(self.matrix), len(self.matrix[0])
        
        # Леса только на земле (не на песке)
        for x in range(rows):
            for y in range(cols):
                if self.matrix[x][y] == BiomesType.LAND:
                    if random.randint(1, 3) == 1:  # 33% шанс леса
                        self.matrix[x][y] = BiomesType.WOODS
        
        # Несколько проходов для сглаживания лесов
        for _ in range(5):
            self.next_generation(BiomesType.LAND, BiomesType.WOODS, [5,6,7,8])
            self.next_generation(BiomesType.WOODS, BiomesType.LAND, [1,2])

    # -------------------- UTILS --------------------
    def create_start_matrix(self):
        """Создание начальной матрицы"""
        rows, cols = settings.Rows, settings.Columns
        
        # 60% земли, 40% моря (больше земли)
        matrix = []
        for x in range(rows):
            row = []
            for y in range(cols):
                if random.randint(1, 100) <= 50:  # 60% земли
                    row.append(BiomesType.LAND)
                else:
                    row.append(BiomesType.SEA)
            matrix.append(row)
        
        return matrix

    def get_color(self, biome):
        """Получить цвет для биома"""
        colors = {
            BiomesType.LAND: settings.COLOR_LAND,      # Зеленый - земля
            BiomesType.SEA: settings.COLOR_SEA,        # Синий - море
            BiomesType.SAND: settings.COLOR_SAND,      # Песочный - пляж
            BiomesType.SEA_SHORE: settings.COLOR_SEA_SHORE,  # Голубой - мелководье
            BiomesType.WOODS: settings.COLOR_WOODS     # Темно-зеленый - лес
        }
        return colors.get(biome, BLACK)

    
    def draw(self, screen, camera_x, camera_y):
        """Отрисовка всех тайлов спрайтами"""
        rows, cols = len(self.matrix), len(self.matrix[0])
        
        start_x = max(0, camera_x // CELL_SIZE)
        start_y = max(0, camera_y // CELL_SIZE)
        end_x = min(cols, (camera_x + WIDTH) // CELL_SIZE + 2)
        end_y = min(rows, (camera_y + HEIGHT) // CELL_SIZE + 2)
        
        # Рисуем землю (только один раз!)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * CELL_SIZE - camera_x
                screen_y = y * CELL_SIZE - camera_y
                
                if -CELL_SIZE <= screen_x < WIDTH and -CELL_SIZE <= screen_y < HEIGHT:
                    biome = self.matrix[y][x]
                    sprite = self.get_biome_sprite(biome, x, y)
                    screen.blit(sprite, (screen_x, screen_y))
        
        # Рисуем деревья ПОВЕРХ земли
        for tree_x, tree_y in self.tree_positions:
            if start_x <= tree_x < end_x and start_y <= tree_y < end_y:
                screen_x = tree_x * CELL_SIZE - camera_x
                screen_y = tree_y * CELL_SIZE - camera_y
                
                offset_x = (CELL_SIZE - self.tree_sprite.get_width()) // 2
                offset_y = (CELL_SIZE - self.tree_sprite.get_height()) // 2
                
                screen.blit(self.tree_sprite, (screen_x + offset_x, screen_y + offset_y))

# Создаем экземпляр биомов
print("Создание карты...")
biomes = Biomes(screen, pg)
biomes.main_render_biomes()

pig = pg.image.load("unknown_game_DL/sprite/Sprite-0001.png")
pig_x, pig_y = 250, 250


# Загрузка спрайта стены
try:
    wall_sprite = pg.image.load("unknown_game_DL/sprite/walll.png")
    wall_sprite = pg.transform.scale(wall_sprite, (CELL_SIZE, CELL_SIZE))
except:
    wall_sprite = pg.Surface((CELL_SIZE, CELL_SIZE))
    wall_sprite.fill(GRAY)


    
# Стены
wall1 = pg.Rect(5 * CELL_SIZE, 5 * CELL_SIZE, CELL_SIZE, CELL_SIZE)
wall2 = pg.Rect(10 * CELL_SIZE, 10 * CELL_SIZE, CELL_SIZE, CELL_SIZE)

# Игровой цикл
clock = pg.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
    
    old_x, old_y = player_size.x, player_size.y
    


    def get_speed_multiplier(biomes, player, CELL_SIZE):
        """Получить множитель скорости в зависимости от тайла под игроком"""
        # Определяем тайл под центром игрока
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        tile_x = player_center_x // CELL_SIZE
        tile_y = player_center_y // CELL_SIZE
        
        # Проверяем границы
        if 0 <= tile_y < len(biomes.matrix) and 0 <= tile_x < len(biomes.matrix[0]):
            biome = biomes.matrix[tile_y][tile_x]
            
            # Если на воде (море или мелководье) - замедление
            if biome in [BiomesType.SEA, BiomesType.SEA_SHORE]:
                return 0.6  # Скорость 60% от обычной
            else:
                return 1.0  # Нормальная скорость
        return 1.0
    
    speed_multiplier = get_speed_multiplier(biomes, player_size, CELL_SIZE)

    keys = pg.key.get_pressed()
    if keys[pg.K_LEFT] or keys[pg.K_a]: 
        player_size.x -= speed * speed_multiplier * dt
    if keys[pg.K_RIGHT] or keys[pg.K_d]: 
        player_size.x += speed * speed_multiplier * dt 
    if keys[pg.K_UP] or keys[pg.K_w]: 
        player_size.y -= speed * speed_multiplier * dt
    if keys[pg.K_DOWN] or keys[pg.K_s]: 
        player_size.y += speed * speed_multiplier * dt
    
    map_width = len(biomes.matrix[0]) * CELL_SIZE
    map_height = len(biomes.matrix) * CELL_SIZE
    
    # Ограничиваем позицию игрока границами карты
    player_size.x = max(0, min(player_size.x, map_width - player_size.width))
    player_size.y = max(0, min(player_size.y, map_height - player_size.height))

    # Коллизии
    if player_size.colliderect(wall1) or player_size.colliderect(wall2):
        player_size.x, player_size.y = old_x, old_y
    for tree_x, tree_y in biomes.tree_positions:
        # Сужаем хитбокс дерева: ствол в центре клетки
        trunk_width = CELL_SIZE // 4
        trunk_height = CELL_SIZE // 3
        trunk_x = tree_x * CELL_SIZE + (CELL_SIZE - trunk_width) // 2
        trunk_y = tree_y * CELL_SIZE + CELL_SIZE // 2  # ствол внизу
        
        tree_rect = pg.Rect(trunk_x, trunk_y, trunk_width, trunk_height)
        if player_size.colliderect(tree_rect):
            player_size.x, player_size.y = old_x, old_y
            break
    # Камера
    camera_x0 = player_size.x - WIDTH // 2
    camera_y0 = player_size.y - HEIGHT // 2
    
    max_camera_x = max(0, len(biomes.matrix[0]) * CELL_SIZE - WIDTH)
    max_camera_y = max(0, len(biomes.matrix) * CELL_SIZE - HEIGHT)
    camera_x0 = max(0, min(camera_x0, max_camera_x))
    camera_y0 = max(0, min(camera_y0, max_camera_y))
    
    #Ограничение позиции игрока, чтобы он не выходил за пределы экрана
    player_x = max(0, min(player_size.x, settings.Columns - pl_si))
    player_y = max(0, min(player_size.y, settings.Rows - pl_si))
        
    # Отрисовка
    screen.fill(BLACK)
    biomes.draw(screen, camera_x0, camera_y0)
    
    # Стены
    screen.blit(wall_sprite, (wall1.x - camera_x0, wall1.y - camera_y0))
    screen.blit(wall_sprite, (wall2.x - camera_x0, wall2.y - camera_y0))
    

    # Игрок
    screen.blit(pl_sprite, (player_size.x - camera_x0, player_size.y - camera_y0))
    
    pg.display.flip()

pg.quit()
sys.exit()