import random
import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pygame
import numpy as np
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table

console = Console()

class GameDatabase:
    def __init__(self, db_name="rpg_game.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    health INTEGER,
                    attack_power INTEGER,
                    level INTEGER,
                    experience INTEGER,
                    quests_completed INTEGER
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    description TEXT,
                    is_completed INTEGER,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)

    def save_player(self, player):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO players (name, health, attack_power, level, experience, quests_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (player.name, player.health, player.attack_power, player.level, player.experience, player.quests_completed))
            player_id = cur.lastrowid
            for item in player.inventory:
                cur.execute("""
                    INSERT INTO inventory (player_id, item_name, quantity)
                    VALUES (?, ?, ?)
                """, (player_id, item.name, item.quantity))
            self.conn.commit()

    def load_player(self, player_name):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM players WHERE name=?", (player_name,))
            row = cur.fetchone()
            if row:
                player = Player(row[1])
                player.health = row[2]
                player.attack_power = row[3]
                player.level = row[4]
                player.experience = row[5]
                player.quests_completed = row[6]
                cur.execute("SELECT item_name, quantity FROM inventory WHERE player_id=?", (row[0],))
                for item_row in cur.fetchall():
                    item = Item(item_row[0], "", item_row[1])
                    player.inventory.append(item)
                cur.execute("SELECT description, is_completed FROM quests WHERE player_id=?", (row[0],))
                for quest_row in cur.fetchall():
                    quest = Quest(quest_row[0])
                    quest.is_completed = quest_row[1]
                    player.quests.append(quest)
                return player
        return None

class Player:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.attack_power = 10
        self.level = 1
        self.experience = 0
        self.quests_completed = 0
        self.inventory = []
        self.quests = []

    def attack(self, enemy):
        damage = random.randint(1, self.attack_power)
        enemy.health -= damage
        return f"{self.name} attacks {enemy.name} for {damage} damage."

    def special_attack(self, enemy):
        damage = random.randint(self.attack_power, self.attack_power * 2)
        enemy.health -= damage
        return f"{self.name} performs a special attack on {enemy.name} for {damage} damage!"

    def add_item(self, item):
        self.inventory.append(item)
        return f"{self.name} picks up {item.name}."

    def show_inventory(self):
        inventory_list = [f"{item.name} (x{item.quantity})" for item in self.inventory]
        return inventory_list if inventory_list else ["No items in inventory."]

    def use_item(self, item_name):
        item = next((i for i in self.inventory if i.name == item_name), None)
        if item:
            effect_message = item.use(self)
            item.quantity -= 1
            if item.quantity <= 0:
                self.inventory.remove(item)
            return f"{self.name} uses {item.name}. {effect_message}"
        return "Item not found in inventory."

    def gain_experience(self, exp):
        self.experience += exp
        if self.experience >= self.level * 10:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.health += 20
        self.attack_power += 5
        self.experience = 0
        return f"{self.name} has leveled up to level {self.level}!"

    def is_alive(self):
        return self.health > 0

    def heal(self):
        self.health = 100

    def accept_quest(self, quest):
        self.quests.append(quest)
        return f"{self.name} accepts quest: {quest.description}"

    def complete_quest(self, quest):
        quest.is_completed = True
        self.quests_completed += 1
        return f"{self.name} completed quest: {quest.description}"

    def display_stats(self):
        table = Table(title=f"{self.name}'s Stats")
        table.add_column("Attribute", justify="right", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_row("Health", str(self.health))
        table.add_row("Attack Power", str(self.attack_power))
        table.add_row("Level", str(self.level))
        table.add_row("Experience", str(self.experience))
        table.add_row("Quests Completed", str(self.quests_completed))
        console.print(table)

    def display_quests(self):
        table = Table(title=f"{self.name}'s Quests")
        table.add_column("Quest", justify="left", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        for quest in self.quests:
            status = "Completed" if quest.is_completed else "Incomplete"
            table.add_row(quest.description, status)
        console.print(table)

class Quest:
    def __init__(self, description):
        self.description = description
        self.is_completed = False

class Enemy:
    def __init__(self, name, health, attack_power, experience_value):
        self.name = name
        self.health = health
        self.attack_power = attack_power
        self.experience_value = experience_value

    def attack(self, player):
        damage = random.randint(1, self.attack_power)
        player.health -= damage
        return f"{self.name} attacks {player.name} for {damage} damage."

    def special_attack(self, player):
        damage = random.randint(self.attack_power, self.attack_power * 2)
        player.health -= damage
        return f"{self.name} performs a special attack on {player.name} for {damage} damage!"

    def is_alive(self):
        return self.health > 0

class Item:
    def __init__(self, name, effect, quantity=1):
        self.name = name
        self.effect = effect
        self.quantity = quantity

    def use(self, player):
        if self.effect == "heal":
            player.health += 20
            return f"{player.name} heals 20 health."
        elif self.effect == "boost":
            player.attack_power += 5
            return f"{player.name} gains 5 attack power."
        elif self.effect == "level_up":
            player.gain_experience(player.level * 10)
            return f"{player.name} gains enough experience to level up!"
        elif self.effect == "random":
            random_effect = random.choice(["heal", "boost", "level_up"])
            return self.use(player)
        return "Nothing happens."

class GameWorld:
    def __init__(self, player):
        self.player = player
        self.enemies = [
            Enemy("Goblin", 30, 5, 5),
            Enemy("Orc", 50, 8, 8),
            Enemy("Dragon", 100, 15, 20),
            Enemy("Troll", 40, 6, 6),
            Enemy("Vampire", 70, 10, 15),
            Enemy("Slime", 20, 3, 3),
            Enemy("Zombie", 60, 7, 10),
            Enemy("Bandit", 50, 9, 8)
        ]
        self.items = [
            Item("Health Potion", "heal"),
            Item("Strength Elixir", "boost"),
            Item("Magic Stone", "boost"),
            Item("Healing Herb", "heal"),
            Item("Experience Scroll", "level_up"),
            Item("Revive Potion", "revive"),
            Item("Energy Drink", "boost"),
            Item("Mystery Box", "random")
        ]
        self.current_enemy = None

    def encounter_enemy(self):
        if self.enemies:
            possible_enemies = [e for e in self.enemies if e.health <= (self.player.level * 20)]
            if not possible_enemies:
                possible_enemies = self.enemies
            self.current_enemy = random.choice(possible_enemies)
            return f"A wild {self.current_enemy.name} appears!"
        return "No more enemies to fight."

    def find_item(self):
        if self.items:
            item = random.choice(self.items)
            self.player.add_item(item)
            self.items.remove(item)
            return f"{self.player.name} finds a {item.name}!"
        return "No more items to find."

    def battle(self):
        battle_log = []
        in_battle = True
        while self.player.is_alive() and self.current_enemy.is_alive():
            action = random.choice(["attack", "special_attack"])
            if action == "attack":
                battle_log.append(self.player.attack(self.current_enemy))
            else:
                battle_log.append(self.player.special_attack(self.current_enemy))

            if self.current_enemy.is_alive():
                action = random.choice(["attack", "special_attack"])
                if action == "attack":
                    battle_log.append(self.current_enemy.attack(self.player))
                else:
                    battle_log.append(self.current_enemy.special_attack(self.player))

        if self.player.is_alive():
            battle_log.append(f"{self.player.name} defeated {self.current_enemy.name}!")
            self.player.gain_experience(self.current_enemy.experience_value)
            level_up_message = self.player.level_up()
            if level_up_message:
                battle_log.append(level_up_message)
            self.enemies.remove(self.current_enemy)
            in_battle = False
        else:
            battle_log.append(f"{self.player.name} has been defeated by {self.current_enemy.name}.")
            in_battle = False
        return battle_log

    def assign_quest(self):
        quests = [
            "Defeat 5 Goblins",
            "Collect 3 Healing Herbs",
            "Find the Magic Stone",
            "Defeat the Dragon",
            "Help the Villager",
            "Find the Lost Sword"
        ]
        quest_description = random.choice(quests)
        quest = Quest(quest_description)
        self.player.accept_quest(quest)
        return f"New quest assigned: {quest.description}"

    def complete_quest(self):
        for quest in self.player.quests:
            if not quest.is_completed:
                self.player.complete_quest(quest)
                return f"Quest completed: {quest.description}"
        return "No quests to complete."

    def display_map(self):
        map_data = np.zeros((10, 10))
        player_pos = (random.randint(0, 9), random.randint(0, 9))
        map_data[player_pos] = 1
        plt.imshow(map_data, cmap="viridis")
        plt.title(f"{self.player.name}'s Map")
        plt.show()

# Pygame setup for immersive view
class PygameApp:
    def __init__(self, player):
        pygame.init()
        self.player = player
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("RPG Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)

    def draw_text(self, text, pos, color=(255, 255, 255)):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, pos)

    def draw_hp_bar(self, entity, pos):
        hp_ratio = entity.health / 100
        pygame.draw.rect(self.screen, (255, 0, 0), (pos[0], pos[1], 100, 20))
        pygame.draw.rect(self.screen, (0, 255, 0), (pos[0], pos[1], 100 * hp_ratio, 20))

    def battle_view(self, enemy):
        in_battle = True
        while in_battle:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            self.screen.fill((0, 0, 0))
            self.draw_text(f"{self.player.name}", (50, 50))
            self.draw_hp_bar(self.player, (50, 100))
            self.draw_text(f"{enemy.name}", (600, 50))
            self.draw_hp_bar(enemy, (600, 100))

            self.draw_text("1. Attack", (50, 400))
            self.draw_text("2. Special Attack", (50, 450))
            self.draw_text("3. Use Item", (50, 500))
            self.draw_text("4. Run", (50, 550))

            keys = pygame.key.get_pressed()
            if keys[pygame.K_1]:
                result = self.player.attack(enemy)
                self.draw_text(result, (300, 400))
                pygame.display.update()
                pygame.time.wait(1000)
                if not enemy.is_alive():
                    result = f"{enemy.name} has been defeated!"
                    self.draw_text(result, (300, 450))
                    pygame.display.update()
                    pygame.time.wait(1000)
                    in_battle = False

            if keys[pygame.K_2]:
                result = self.player.special_attack(enemy)
                self.draw_text(result, (300, 400))
                pygame.display.update()
                pygame.time.wait(1000)
                if not enemy.is_alive():
                    result = f"{enemy.name} has been defeated!"
                    self.draw_text(result, (300, 450))
                    pygame.display.update()
                    pygame.time.wait(1000)
                    in_battle = False

            if keys[pygame.K_3]:
                inventory = self.player.show_inventory()
                for i, item in enumerate(inventory):
                    self.draw_text(f"{i+1}. {item}", (300, 300 + i * 50))
                pygame.display.update()
                pygame.time.wait(2000)

            if keys[pygame.K_4]:
                in_battle = False

            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()

class RPGGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Game")
        self.db = GameDatabase()

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.player_name_label = ttk.Label(root, text="Enter your character's name:")
        self.player_name_label.pack(pady=5)
        self.player_name_entry = ttk.Entry(root)
        self.player_name_entry.pack(pady=5)
        self.start_button = ttk.Button(root, text="Start Game", command=self.start_game)
        self.start_button.pack(pady=5)

        self.load_button = ttk.Button(root, text="Load Game", command=self.load_game)
        self.load_button.pack(pady=5)

        self.game_frame = ttk.Frame(root)
        self.game_frame.pack(pady=20)

    def start_game(self):
        player_name = self.player_name_entry.get()
        if player_name:
            self.player = Player(player_name)
            self.world = GameWorld(self.player)
            self.db.save_player(self.player)
            self.setup_game_ui()

    def load_game(self):
        player_name = self.player_name_entry.get()
        player = self.db.load_player(player_name)
        if player:
            self.player = player
            self.world = GameWorld(self.player)
            self.setup_game_ui()
        else:
            messagebox.showinfo("Error", "Player not found.")

    def setup_game_ui(self):
        self.player_name_label.pack_forget()
        self.player_name_entry.pack_forget()
        self.start_button.pack_forget()
        self.load_button.pack_forget()

        self.status_label = ttk.Label(self.game_frame, text=f"Player: {self.player.name} | Health: {self.player.health} | Attack Power: {self.player.attack_power} | Level: {self.player.level}")
        self.status_label.pack()

        self.action_frame = ttk.Frame(self.game_frame)
        self.action_frame.pack(pady=10)

        self.explore_button = ttk.Button(self.action_frame, text="Explore", command=self.explore)
        self.explore_button.pack(side=tk.LEFT, padx=5)
        self.show_inventory_button = ttk.Button(self.action_frame, text="Show Inventory", command=self.show_inventory)
        self.show_inventory_button.pack(side=tk.LEFT, padx=5)
        self.use_item_button = ttk.Button(self.action_frame, text="Use Item", command=self.use_item)
        self.use_item_button.pack(side=tk.LEFT, padx=5)
        self.heal_button = ttk.Button(self.action_frame, text="Heal", command=self.heal)
        self.heal_button.pack(side=tk.LEFT, padx=5)
        self.assign_quest_button = ttk.Button(self.action_frame, text="Assign Quest", command=self.assign_quest)
        self.assign_quest_button.pack(side=tk.LEFT, padx=5)
        self.complete_quest_button = ttk.Button(self.action_frame, text="Complete Quest", command=self.complete_quest)
        self.complete_quest_button.pack(side=tk.LEFT, padx=5)
        self.stats_button = ttk.Button(self.action_frame, text="Show Stats", command=self.show_stats)
        self.stats_button.pack(side=tk.LEFT, padx=5)
        self.map_button = ttk.Button(self.action_frame, text="Show Map", command=self.show_map)
        self.map_button.pack(side=tk.LEFT, padx=5)

        self.output_text = tk.Text(self.game_frame, height=20, width=80)
        self.output_text.pack()

    def explore(self):
        action = random.choice(["encounter", "item"])
        if action == "encounter":
            encounter_message = self.world.encounter_enemy()
            self.output_text.insert(tk.END, encounter_message + "\n")
            if self.world.current_enemy:
                pygame_app = PygameApp(self.player)
                battle_log = pygame_app.battle_view(self.world.current_enemy)
                for log in battle_log:
                    self.output_text.insert(tk.END, log + "\n")
        elif action == "item":
            item_message = self.world.find_item()
            self.output_text.insert(tk.END, item_message + "\n")

        self.update_status()

    def show_inventory(self):
        inventory = self.player.show_inventory()
        self.output_text.insert(tk.END, f"{self.player.name}'s Inventory:\n")
        for item in inventory:
            self.output_text.insert(tk.END, f"- {item}\n")

    def use_item(self):
        if self.player.inventory:
            item_name = self.player.inventory[0].name  # Just use the first item for simplicity
            use_item_message = self.player.use_item(item_name)
            self.output_text.insert(tk.END, use_item_message + "\n")
        else:
            self.output_text.insert(tk.END, "No items in inventory.\n")

        self.update_status()

    def heal(self):
        if self.world.current_enemy and self.world.current_enemy.is_alive():
            self.output_text.insert(tk.END, "Cannot heal during battle.\n")
        else:
            self.player.heal()
            self.update_status()
            self.output_text.insert(tk.END, f"{self.player.name} has been fully healed.\n")

    def assign_quest(self):
        quest_message = self.world.assign_quest()
        self.output_text.insert(tk.END, quest_message + "\n")

    def complete_quest(self):
        complete_message = self.world.complete_quest()
        self.output_text.insert(tk.END, complete_message + "\n")

    def show_stats(self):
        self.player.display_stats()

    def show_map(self):
        self.world.display_map()

    def update_status(self):
        self.status_label.config(text=f"Player: {self.player.name} | Health: {self.player.health} | Attack Power: {self.player.attack_power} | Level: {self.player.level}")
        if not self.player.is_alive():
            messagebox.showinfo("Game Over", "You have been defeated.")
            self.root.quit()

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = RPGGameApp(root)
    root.mainloop()
