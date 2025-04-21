# assets.py
import pygame

def load_assets(SCREEN_WIDTH, SCREEN_HEIGHT):
    CAR_IMAGE = pygame.image.load("PNG/App/car7.png").convert_alpha()
    PLAY_IMG = pygame.image.load("PNG/App/PlayButton.png")
    EMPTY_BTN_IMG = pygame.image.load("PNG/App/SmallEmptyButton.png")

    PEDESTRIAN_IMAGES = [
        pygame.image.load("./PNG/Other/Person_BlueBlack1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_RedBlack1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_YellowBrown2.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_RedBlond1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_PurpleBrown1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_OrangeBrown1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_GreenBlack2.png").convert_alpha(),
    ]

    button_width, button_height = PLAY_IMG.get_size()
    BUTTON_X = (SCREEN_WIDTH - button_width) // 2
    BUTTON_Y = (SCREEN_HEIGHT - button_height) // 2

    return CAR_IMAGE, PLAY_IMG, EMPTY_BTN_IMG, PEDESTRIAN_IMAGES, BUTTON_X, BUTTON_Y
