import pygame
import random
from pygame.locals import *
import os

pygame.init()
screen = pygame.display.set_mode((1024, 768))
pygame.display.set_caption("Караван")
font = pygame.font.SysFont('Arial', 24)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CARD_COLOR = (200, 200, 255)
SPECIAL_CARD = (255, 200, 200)
CARAVAN_COLOR = (200, 255, 200)

class Card:
    def __init__(self, value, suit, source):
        self.value = value
        self.suit = suit
        self.source = source
        self.face_up = True
        self.width = 80
        self.height = 120
        self.image = self.load_image()

    def load_image(self):
        if self.value == "Joker":
            suit_str = "Other"
            number_str = "Joker"
        else:
            suit_str = self.suit
            number_str = str(self.value)

        filename = f"Suit={suit_str}, Number={number_str}.png"
        path = os.path.join("cards", filename)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return None


    def is_special(self):
        return isinstance(self.value, str)

    def is_joker(self):
        return self.value == "Joker"

    def get_numeric_value(self):
        if isinstance(self.value, int):
            return self.value
        return 0

    def __str__(self):
        return f"{self.value} of {self.suit} ({self.source})"

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
        for _ in range(8):
            self.draw_card()

    def play_card_to_caravan(self, card_index, caravan_index):
        if 0 <= card_index < len(self.hand) and 0 <= caravan_index < 3:
            card = self.hand[card_index]
            caravan = self.caravans[caravan_index]

            if card.is_joker():
                caravan.clear()
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
                if caravan:
                    last_card = caravan[-1]
                    # Копируем карту, но обязательно с таким же значением
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
        if ascending:
            return card.value > last_card.value
        else:
            return card.value < last_card.value

    def is_ascending(self, caravan):
        values = [c.get_numeric_value() for c in caravan if isinstance(c.value, int)]
        if len(values) < 2:
            return None
        return values[-1] > values[-2]

class Game:
    def __init__(self):
        self.deck1 = Deck("Player1")
        self.deck2 = Deck("Player2")
        self.player1 = Player("Player1", self.deck1, is_ai=False)
        self.player2 = Player("Player2", self.deck2, is_ai=True)
        self.current_player = self.player1
        self.opponent = self.player2
        self.running = True
        self.selected_card_index = None
        self.selected_caravan_index = None
        self.ai_thinking = False
        self.ai_timer = 0

        self.player1.start_game()
        self.player2.start_game()

    def switch_turn(self):
        self.current_player, self.opponent = self.opponent, self.current_player
        self.selected_card_index = None
        self.selected_caravan_index = None
        self.ai_thinking = False
        self.ai_timer = 0

    def caravan_value(self, caravan):
        return sum(card.get_numeric_value() for card in caravan if isinstance(card.value, int))

    def draw_cards(self):
        self.current_player.draw_card()

    def draw_card_visual(self, card, x, y):
        if card.image:
            img = pygame.transform.scale(card.image, (card.width, card.height))
            screen.blit(img, (x, y))
            pygame.draw.rect(screen, BLACK, (x, y, card.width, card.height), 2)
        else:
            color = SPECIAL_CARD if card.is_special() else CARD_COLOR
            pygame.draw.rect(screen, color, (x, y, card.width, card.height))
            pygame.draw.rect(screen, BLACK, (x, y, card.width, card.height), 2)
            value_text = font.render(str(card.value), True, BLACK)
            suit_text = font.render(str(card.suit) if card.suit else "", True, BLACK)
            screen.blit(value_text, (x + 5, y + 5))
            screen.blit(suit_text, (x + 5, y + 30))

    def draw_caravans(self, player, y_offset):
        for i, caravan in enumerate(player.caravans):
            x = 150 + i * 300
            y = y_offset
            for j, card in enumerate(caravan):
                self.draw_card_visual(card, x, y + j * 25)
            value = self.caravan_value(caravan)
            value_text = font.render(f"Value: {value}", True, BLACK)
            screen.blit(value_text, (x, y + len(caravan) * 25 + 5))

    def draw_hand(self, player, y):
        for i, card in enumerate(player.hand):
            self.draw_card_visual(card, 50 + i * 90, y)

    def ai_move(self):
        # ИИ выбирает первый подходящий ход: карту + караван
        for card_index, card in enumerate(self.current_player.hand):
            for caravan_index in range(3):
                if self.current_player.play_card_to_caravan(card_index, caravan_index):
                    self.current_player.draw_card()
                    self.switch_turn()
                    return
                
    def check_win(self, player):
        sold = 0
        for caravan in player.caravans:
            value = self.caravan_value(caravan)
            if 21 <= value <= 26:
                sold += 1
        return sold >= 2

    def run(self):
        clock = pygame.time.Clock()
        winner = None
        while self.running:
            dt = clock.tick(30)

            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == MOUSEBUTTONDOWN and not self.current_player.is_ai:
                    mx, my = pygame.mouse.get_pos()
                    if my > 600:
                        index = (mx - 50) // 90
                        if 0 <= index < len(self.current_player.hand):
                            self.selected_card_index = index
                    elif 300 < my < 500:
                        index = (mx - 150) // 300
                        if 0 <= index < 3:
                            self.selected_caravan_index = index
                            if self.selected_card_index is not None:
                                success = self.current_player.play_card_to_caravan(
                                    self.selected_card_index,
                                    self.selected_caravan_index
                                )
                                if success:
                                    self.current_player.draw_card()
                                    self.switch_turn()

            # Если ход ИИ, ждем 0.7 секунды, чтобы имитировать "мышление"
            if self.current_player.is_ai:
                self.ai_timer += dt
                if self.ai_timer > 700:
                    self.ai_move()

            # --- Проверка победы ---
            if self.check_win(self.player1):
                winner = self.player1.name
                self.running = False
            elif self.check_win(self.player2):
                winner = self.player2.name
                self.running = False

            screen.fill(WHITE)
            self.draw_hand(self.player1, 620)
            self.draw_hand(self.player2, 100)
            self.draw_caravans(self.player1, 400)
            self.draw_caravans(self.player2, 200)
            turn_text = font.render(f"Turn: {self.current_player.name}", True, BLACK)
            screen.blit(turn_text, (10, 10))

            if winner:
                win_text = font.render(f"Победил: {winner}!", True, (255, 0, 0))
                screen.blit(win_text, (400, 50))

            pygame.display.flip()

        # Показываем победителя 2 секунды перед выходом
        if winner:
            pygame.time.wait(2000)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
