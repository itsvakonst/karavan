import pygame
import random
from pygame.locals import *

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((1024, 768))
pygame.display.set_caption("Караван")
font = pygame.font.SysFont('Arial', 24)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CARD_COLOR = (200, 200, 255)
SPECIAL_CARD = (255, 200, 200)
CARAVAN_COLOR = (200, 255, 200)
PLAYER_HAND_AREA = (0, 600, 1024, 168)


class Card:
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit
        self.face_up = True
        self.width = 80
        self.height = 120

    def is_special(self):
        return isinstance(self.value, str)

    def __str__(self):
        return f"{self.value} of {self.suit}"


class Deck:
    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        values = list(range(1, 11)) + ["King", "Queen", "Jack"]
        for suit in suits:
            for value in values:
                self.cards.append(Card(value, suit))
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None


class Caravan:
    def __init__(self):
        self.cards = []
        self.direction = None
        self.suit = None
        self.total = 0
        self.x = 0
        self.y = 0

    def add_card(self, card):
        if not self.validate_card(card):
            return False

        self.cards.append(card)
        self.update_total()
        return True

    def validate_card(self, card):
        if not self.cards:
            return not card.is_special()
        return True

    def update_total(self):
        self.total = 0
        king_multiplier = 1

        for i, card in enumerate(self.cards):
            if isinstance(card.value, int):
                self.total += card.value * king_multiplier
                king_multiplier = 1
            elif card.value == "King" and i > 0:
                king_multiplier = 2

    def reset(self):
        discarded = self.cards
        self.__init__()
        return discarded

    def draw(self, surface, x, y):
        self.x, self.y = x, y
        pygame.draw.rect(surface, CARAVAN_COLOR, (x, y, 300, 150))
        for i, card in enumerate(self.cards):
            card_x = x + i * 30 if i < 8 else x + (i - 8) * 30
            card_y = y + 20 if i < 8 else y + 50
            self.draw_card(surface, card, card_x, card_y)

        text = font.render(f"Очки: {self.total}", True, BLACK)
        surface.blit(text, (x + 10, y + 10))

    def draw_card(self, surface, card, x, y):
        color = SPECIAL_CARD if card.is_special() else CARD_COLOR
        pygame.draw.rect(surface, color, (x, y, card.width, card.height))
        text = font.render(str(card.value), True, BLACK)
        surface.blit(text, (x + 10, y + 50))


class Player:
    def __init__(self, name, is_ai=False):
        self.name = name
        self.hand = []
        self.caravans = [Caravan(), Caravan(), Caravan()]
        self.is_ai = is_ai
        self.selected_card = None

    def draw_card(self, deck, count=1):
        for _ in range(count):
            if len(self.hand) < 5 and deck.cards:
                self.hand.append(deck.draw())

    def play_card(self, hand_index, caravan_index):
        if 0 <= hand_index < len(self.hand) and 0 <= caravan_index < 3:
            card = self.hand.pop(hand_index)
            return self.caravans[caravan_index].add_card(card)
        return False

    def has_won(self):
        return all(21 <= caravan.total <= 26 for caravan in self.caravans if caravan.cards)

    def draw_hand(self, surface):
        for i, card in enumerate(self.hand):
            x = 100 + i * 100
            y = 620
            color = (255, 255, 0) if self.selected_card == i else (
                CARD_COLOR if isinstance(card.value, int) else SPECIAL_CARD)
            pygame.draw.rect(surface, color, (x, y, card.width, card.height))
            text = font.render(str(card.value), True, BLACK)
            surface.blit(text, (x + 10, y + 50))


class Game:
    def __init__(self):
        self.deck = Deck()
        self.player = Player("Игрок")
        self.opponent = Player("Оппонент", is_ai=True)
        self.current_player = self.player
        self.message = ""
        self.setup_game()

    def setup_game(self):
        self.player.draw_card(self.deck, 8)
        self.opponent.draw_card(self.deck, 8)

    def switch_player(self):
        self.current_player = self.opponent if self.current_player == self.player else self.player

    def ai_turn(self):
        if not self.current_player.is_ai:
            return

        for i, caravan in enumerate(self.current_player.caravans):
            for j, card in enumerate(self.current_player.hand):
                if caravan.add_card(card):
                    self.current_player.hand.pop(j)
                    break

        self.switch_player()

    def check_game_over(self):
        if self.player.has_won():
            return "Игрок победил!"
        elif self.opponent.has_won():
            return "Оппонент победил!"
        return None

    def handle_click(self, pos):
        if self.current_player.is_ai:
            return

        x, y = pos

        # Проверка клика по картам в руке
        for i, card in enumerate(self.player.hand):
            card_x = 100 + i * 100
            card_y = 620
            if card_x <= x <= card_x + card.width and card_y <= y <= card_y + card.height:
                self.player.selected_card = i
                return

        # Проверка клика по караванам
        if self.player.selected_card is not None:
            for i, caravan in enumerate(self.player.caravans):
                if caravan.x <= x <= caravan.x + 300 and caravan.y <= y <= caravan.y + 150:
                    if self.player.play_card(self.player.selected_card, i):
                        self.switch_player()
                    self.player.selected_card = None
                    return


def main():
    game = Game()
    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill(WHITE)

        # Отрисовка караванов игрока
        for i, caravan in enumerate(game.player.caravans):
            caravan.draw(screen, 100 + i * 320, 400)

        # Отрисовка караванов оппонента
        for i, caravan in enumerate(game.opponent.caravans):
            caravan.draw(screen, 100 + i * 320, 100)

        # Отрисовка руки игрока
        game.player.draw_hand(screen)

        # Отрисовка информации
        text = font.render(f"Ход: {game.current_player.name}", True, BLACK)
        screen.blit(text, (400, 50))

        if game.message:
            text = font.render(game.message, True, (255, 0, 0))
            screen.blit(text, (400, 80))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                game.handle_click(event.pos)

        if game.current_player.is_ai:
            pygame.time.delay(1000)  # Задержка для хода ИИ
            game.ai_turn()

        result = game.check_game_over()
        if result:
            game.message = result
            # running = False  # Раскомментировать для автоматического завершения

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()