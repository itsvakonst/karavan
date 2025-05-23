import pygame
import random
import os
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()
pygame.display.set_caption("Караван")
font = pygame.font.SysFont('Impact', 24)
large_font = pygame.font.SysFont('Impact', 70)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CARD_COLOR = (200, 200, 255)

SPECIAL_CARD = (255, 200, 200)
CARAVAN_COLOR = (200, 255, 200)

BUTTON_COLOR = (50, 150, 255)
BUTTON_HOVER = (80, 180, 255)

background_image = pygame.image.load("textures/background.jpg").convert()

class Button:
    def __init__(self, rect, text, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action

    def draw(self, surf):
        mouse = pygame.mouse.get_pos()
        color = BUTTON_HOVER if self.rect.collidepoint(mouse) else BUTTON_COLOR
        pygame.draw.rect(surf, color, self.rect)
        pygame.draw.rect(surf, BLACK, self.rect, 2)
        label = font.render(self.text, True, BLACK)
        surf.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2,
                          self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Card:
    def __init__(self, value, suit, source):
        self.value = value
        self.suit = suit
        self.source = source
        self.face_up = True
        self.width = 80
        self.height = 120
        self.x, self.y = 0, 0
        self.target_x, self.target_y = 0, 0
        self.image = self.load_image()

    def load_image(self):
        if self.value == "Joker":
            suit_str = "Other"
            number_str = "Joker"
        else:
            suit_str = self.suit
            number_str = str(self.value)
        path = os.path.join("cards", f"Suit={suit_str}, Number={number_str}.png")
        return pygame.image.load(path).convert_alpha() if os.path.exists(path) else None

    def is_special(self):
        return isinstance(self.value, str)

    def is_joker(self):
        return self.value == "Joker"

    def get_numeric_value(self):
        return self.value if isinstance(self.value, int) else 0

    def update_position(self):
        speed = 0.2
        self.x += (self.target_x - self.x) * speed
        self.y += (self.target_y - self.y) * speed

class Deck:
    def __init__(self, name):
        self.name = name
        self.cards = []
        self.build()

    def build(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        values = list(range(1, 11)) + ["Jack", "Queen", "King"]
        for suit in suits:
            for value in values:
                self.cards.append(Card(value, suit, self.name))
        for _ in range(2):
            self.cards.append(Card("Joker", None, self.name))
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

class Player:
    def __init__(self, name, deck, is_ai=False):
        self.name = name
        self.deck = deck
        self.hand = []
        self.caravans = [[], [], []]
        self.is_ai = is_ai

    def draw_card(self):
        if len(self.hand) < 8:
            card = self.deck.draw()
            if card:
                self.hand.append(card)

    def start_game(self):
        self.hand.clear()
        self.caravans = [[], [], []]
        for _ in range(8):
            self.draw_card()

    def play_card_to_caravan(self, card_index, caravan_index):
        if 0 <= card_index < len(self.hand) and 0 <= caravan_index < 3:
            card = self.hand[card_index]
            caravan = self.caravans[caravan_index]
            if card.is_joker():
                if caravan:
                    caravan.clear()
                else:
                    return False
            elif card.value == "Jack":
                if caravan:
                    caravan.pop()
                else:
                    return False
            elif card.value == "Queen":
                if caravan:
                    caravan.reverse()
                else:
                    return False
            elif card.value == "King":
                if caravan and isinstance(caravan[-1].value, int):
                    last_card = caravan[-1]
                    caravan.append(Card(last_card.value, last_card.suit, last_card.source))
                else:
                    return False
            elif isinstance(card.value, int):
                if self.valid_numeric_play(card, caravan):
                    caravan.append(card)
                else:
                    return False
            else:
                return False
            self.hand.pop(card_index)
            return True
        return False

    def valid_numeric_play(self, card, caravan):
        if not caravan:
            return True
        last_card = caravan[-1]
        if not isinstance(last_card.value, int):
            return False
        ascending = self.is_ascending(caravan)
        if ascending is None:
            return True
        return card.value > last_card.value if ascending else card.value < last_card.value

    def is_ascending(self, caravan):
        values = [c.get_numeric_value() for c in caravan if isinstance(c.value, int)]
        if len(values) < 2:
            return None
        if all(x < y for x, y in zip(values, values[1:])):
            return True
        elif all(x > y for x, y in zip(values, values[1:])):
            return False
        return None

class Game:
    def __init__(self):
        self.running = True
        self.show_menu = True
        self.show_result = False
        self.result_text = ""
        self.buttons = []
        self.create_menu_buttons()

    def create_menu_buttons(self):
        self.buttons = [
            Button((width//2 - 100, height//2 - 60, 200, 50), "Начать игру", self.start_game),
            Button((width//2 - 100, height//2 + 10, 200, 50), "Выйти", self.exit_game)
        ]

    def create_result_buttons(self):
        self.buttons = [
            Button((width//2 - 100, height//2 + 10, 200, 50), "Начать заново", self.start_game),
            Button((width//2 - 100, height//2 + 70, 200, 50), "Выйти", self.exit_game)
        ]

    def start_game(self):
        self.deck1 = Deck("Player1")
        self.deck2 = Deck("Player2")
        self.player1 = Player("Player1", self.deck1)
        self.player2 = Player("Player2", self.deck2, is_ai=True)
        self.current_player = self.player1
        self.opponent = self.player2
        self.selected_card_index = None
        self.selected_caravan_index = None
        self.ai_timer = 0
        self.winner = None
        self.show_menu = False
        self.show_result = False
        self.player1.start_game()
        self.player2.start_game()
        self.create_game_buttons()

    def create_game_buttons(self):
        self.buttons = [
            Button((width - 220, height - 60, 200, 40), "Начать заново", self.start_game)
        ]

    def exit_game(self):
        self.running = False

    def switch_turn(self):
        self.current_player, self.opponent = self.opponent, self.current_player
        self.selected_card_index = None
        self.selected_caravan_index = None
        self.ai_timer = 0

    def caravan_value(self, caravan):
        return sum(card.get_numeric_value() for card in caravan if isinstance(card.value, int))

    def draw_card_visual(self, card):
        card.update_position()
        if card.image:
            img = pygame.transform.scale(card.image, (card.width, card.height))
            screen.blit(img, (card.x, card.y))
        else:
            color = SPECIAL_CARD if card.is_special() else CARD_COLOR
            pygame.draw.rect(screen, color, (card.x, card.y, card.width, card.height))
            pygame.draw.rect(screen, BLACK, (card.x, card.y, card.width, card.height), 2)
            screen.blit(font.render(str(card.value), True, BLACK), (card.x + 5, card.y + 5))
            if card.suit:
                screen.blit(font.render(str(card.suit), True, BLACK), (card.x + 5, card.y + 30))

    def draw_caravans(self, player, y_offset):
        for i, caravan in enumerate(player.caravans):
            x = 150 + i * 300
            y = y_offset
            if not caravan:
                pygame.draw.rect(screen, WHITE, (x, y, 80, 120), 3)
            for j, card in enumerate(caravan):
                card.target_x, card.target_y = x, y + j * 25
                self.draw_card_visual(card)
            value = self.caravan_value(caravan)
            screen.blit(font.render(f"Сумма: {value}", True, WHITE), (x, y + 130 + len(caravan) * 25))

    def draw_hand(self, player, y):
        for i, card in enumerate(player.hand):
            card.target_x, card.target_y = 50 + i * 90, y
            self.draw_card_visual(card)

    def ai_move(self):
        best_score = -1
        best_move = None  # (card_index, caravan_index)

        for card_index, card in enumerate(self.current_player.hand):
            for caravan_index in range(3):
                caravan = self.current_player.caravans[caravan_index]

                # Пропускаем караваны уже "закрытые" (сумма 21-26)
                current_value = self.caravan_value(caravan)
                if 21 <= current_value <= 26:
                    continue

                temp_caravan = caravan.copy()

                if card.is_joker():
                    if caravan:
                        temp_caravan = []
                    else:
                        continue
                elif card.value == "Jack":
                    if caravan:
                        temp_caravan = caravan[:-1]
                    else:
                        continue
                elif card.value == "Queen":
                    if caravan:
                        temp_caravan = caravan[::-1]
                    else:
                        continue
                elif card.value == "King":
                    if caravan and isinstance(caravan[-1].value, int):
                        last_card = caravan[-1]
                        temp_caravan.append(Card(last_card.value, last_card.suit, last_card.source))
                    else:
                        continue
                elif isinstance(card.value, int):
                    if not self.current_player.valid_numeric_play(card, caravan):
                        continue
                    temp_caravan.append(card)
                else:
                    continue

                score = self.caravan_value(temp_caravan)

                if 21 <= score <= 26:
                    best_move = (card_index, caravan_index)
                    best_score = score
                    break

                # Добавим небольшой штраф, если караван уже близок к 21, чтобы стимулировать развитие других
                penalty = 0
                if current_value >= 18:
                    penalty = 5  # штраф

                adjusted_score = score - penalty

                if adjusted_score <= 26 and adjusted_score > best_score:
                    best_score = adjusted_score
                    best_move = (card_index, caravan_index)

            if best_score == 26:
                break

        if best_move:
            card_index, caravan_index = best_move
            if self.current_player.play_card_to_caravan(card_index, caravan_index):
                self.current_player.draw_card()
                self.switch_turn()



    def check_win(self, player):
        return sum(1 for caravan in player.caravans if 21 <= self.caravan_value(caravan) <= 26) >= 2

    def draw_buttons(self):
        for button in self.buttons:
            button.draw(screen)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(30)
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for button in self.buttons:
                        if button.is_clicked((mx, my)):
                            button.action()
                            break
                    if not self.show_menu and not self.show_result and not self.current_player.is_ai:
                        if my > height - 160:
                            index = (mx - 50) // 90
                            if 0 <= index < len(self.current_player.hand):
                                self.selected_card_index = index
                        elif height//2 - 100 < my < height//2 + 200:
                            index = (mx - 150) // 300
                            if 0 <= index < 3 and self.selected_card_index is not None:
                                if self.current_player.play_card_to_caravan(self.selected_card_index, index):
                                    self.current_player.draw_card()
                                    self.switch_turn()

            screen.blit(pygame.transform.scale(background_image, (width, height)), (0, 0))

            if self.show_menu:
                title = large_font.render("КАРАВАН", True, WHITE)
                screen.blit(title, (width//2 - title.get_width()//2, 200))
                self.draw_buttons()
            elif self.show_result:
                result = large_font.render(self.result_text, True, WHITE)
                screen.blit(result, (width//2 - result.get_width()//2, 200))
                self.draw_buttons()
            else:
                if self.current_player.is_ai:
                    self.ai_timer += dt
                    if self.ai_timer > 700:
                        self.ai_move()

                if self.check_win(self.player1):
                    self.result_text = "Победил Игрок 1!"
                    self.show_result = True
                    self.create_result_buttons()
                elif self.check_win(self.player2):
                    self.result_text = "Победил Игрок 2!"
                    self.show_result = True
                    self.create_result_buttons()

                self.draw_hand(self.player1, height - 140)
                self.draw_hand(self.player2, 100)
                self.draw_caravans(self.player1, height//2 + 20)
                self.draw_caravans(self.player2, height//2 - 200)
                screen.blit(font.render(f"Ход: {self.current_player.name}", True, WHITE), (10, 10))
                self.draw_buttons()

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    Game().run()
