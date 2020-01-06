# -----------------------------------------------------------------------------
# Copyright(c) 2017-2020 United Technologies Research Center Ireland Limited.
# This document/file and its contents are property of United Technologies Research
# Center Ireland Limited. You may not possess, use, copy or disclose this
# document/file or any information in it, for any purpose without United Technologies
# Research Center Ireland Limited’s express written permission. Neither receipt
# nor possession of this document/file alone, from any source, constitutes such
# permission. Possession, use, copying or disclosure by anyone without UTRC-I
# express written permission is not authorized and may result in criminal and/or
# civil liability.
#
# All rights reserved.
#
# Classification: EU ECCN: NSR, US ECCN: EAR99
# -----------------------------------------------------------------------------
#
# Author: Riccardo Orizio
# Date: Thu 02 Jan 2020
# Description: 
#


from abc import abstractmethod
import pygame
import random

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CLASSES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def show( self ) -> None:
    """

    :return:
    :rtype:
    """

    pygame.init()
    pygame.display.init()
    game_font = pygame.font.Font( None, 16 )
    print( pygame.display.Info() )
    game_display = pygame.display.set_mode( ( 1024, 768 ) )
    pygame.display.set_caption( "Nonogram" )
    game_clock = pygame.time.Clock()
    active_elements = []

    cell_size = 40
    cell_space = 1
    block_space = 5
    left_space = 100
    top_space = 100

    closed = False
    while not closed:
        # White background
        game_display.fill( ( 255, 255, 255 ) )

        # Game board black background
        pygame.draw.rect( game_display,
                          ( 0, 0, 0 ),
                          pygame.Rect( ( left_space - block_space, top_space - block_space ),
                                       ( self.size * ( cell_size + cell_space ) +
                                         ( int( self.size / 5 ) + 1 ) * block_space,
                                         self.size * ( cell_size + cell_space ) +
                                         ( int( self.size / 5 ) + 1 ) * block_space ) ) )

        # Board cells
        for i in range( self.size ):
            for j in range( self.size ):
                position = ( i * cell_size + i * cell_space + int( i / 5 ) * block_space + left_space,
                             j * cell_size + j * cell_space + int( j / 5 ) * block_space + top_space )
                size = ( cell_size, cell_size )

                pygame.draw.rect( game_display,
                                  ( 255, 255, 255 ),
                                  pygame.Rect( position, size ) )

        # Board constraints
        for i in range( self.size ):
            # Row
            active_elements.append(
                    InputBox( 0,
                              i * cell_size + i * cell_space + int( i / 5 ) * block_space + left_space,
                              75,
                              cell_size,
                              font=pygame.font.Font( None, 16 ),
                              color=( 0, 255, 0 ) ) )

            # Column
            active_elements.append(
                    InputBox( i * cell_size + i * cell_space + int( i / 5 ) * block_space + top_space,
                              0,
                              cell_size,
                              75,
                              font=pygame.font.Font( None, 16 ),
                              color=( 0, 255, 0 ) ) )

        # Solve button
        active_elements.append( Button( 900, 700, 75, 25, "Solve", font=game_font, function=sbra ) )
        #   pygame.draw.rect( game_display, ( 0, 0, 255 ), ( 900, 700, 75, 25 ) )
        #   solve_text = pygame.font.Font( "freesansbold.ttf", 20 )
        #   text_surface = solve_text.render( "Solve", True, ( 0, 0, 0 ) )
        #   text_rect = text_surface.get_rect()
        #   text_rect.center = ( 900 + 75 / 2, 700 + 25 / 2 )
        #   game_display.blit( text_surface, text_rect )

        # Drawing all the elements
        for element in active_elements:
            element.update()
            element.draw( game_display )

        # Event handling
        for event in pygame.event.get():
            print( event )

            if event.type == pygame.QUIT:
                closed = True
            for element in active_elements:
                element.handle_event( event )

        # Re-Draw
        pygame.display.update()
        game_clock.tick( 30 )

    pygame.quit()


class Button:

    def __init__( self, x, y, w, h, text, function=None, font=None, color=None ):
        if color is None:
            color = ( 0, 0, 255 )
        if font is None:
            font = pygame.font.Font( None, 16 )

        self.rect = pygame.Rect( x, y, w, h )
        self.color = color
        self.text = text
        self.font = font
        self.txt_surface = font.render( self.text, True, ( 0, 0, 0 ) )
        self.active = False
        self.function = function

    def handle_event( self, event: pygame.event ):
        print( "Button handler {}".format( pygame.mouse.get_pos() ) )
        if event.type == pygame.MOUSEBUTTONDOWN:
            print( "Button Mouse down" )
            if self.rect.collidepoint( event.pos ):
                print( "Button collide {}".format( self.color ), end="" )
                self.color = ( random.randrange( 255 ), random.randrange( 255 ), random.randrange( 255 ) )
                print( self.color )

    def update( self ):
        pass

    def draw( self, display: pygame.display ):
        pygame.draw.rect( display, self.color, self.rect )


class InputBox:

    def __init__( self, x, y, w, h, text="", font=None, color=None ):
        if color is None:
            color = ( 255, 255, 255 )
        if font is None:
            font = pygame.font.Font( None, 16 )

        self.rect = pygame.Rect( x, y, w, h )
        self.color = color
        self.text = text
        self.font = font
        self.txt_surface = font.render( self.text, True, ( 0, 0, 0 ) )
        self.active = False

    def handle_event( self, event: pygame.event ):
        """

        :param event:
        :type event:
        :return:
        :rtype:
        """

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint( event.pos ):
                self.active = not self.active
            else:
                self.active = False

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print( self.text )
                    self.text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[ :-1 ]
                elif constraint_allowed_values( event.key ):
                    self.text += event.unicode

                self.txt_surface = self.font.render( self.text, True, self.color )

    def update( self ):
        #   self.rect.w = max( self.rect.w, self.txt_surface.get_width() + 10 )
        pass

    def draw( self, display ):
        display.blit( self.txt_surface, ( self.rect.x, self.rect.y ) )
        pygame.draw.rect( display, self.color, self.rect )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def is_keyboard_number( event_key: str ) -> bool:
    """

    :param event_key:
    :type event_key:
    :return:
    :rtype:
    """

    if event_key == pygame.K_0 or \
            event_key == pygame.K_1 or \
            event_key == pygame.K_2 or \
            event_key == pygame.K_3 or \
            event_key == pygame.K_4 or \
            event_key == pygame.K_5 or \
            event_key == pygame.K_6 or \
            event_key == pygame.K_7 or \
            event_key == pygame.K_8 or \
            event_key == pygame.K_9 or \
            event_key == pygame.K_KP0 or \
            event_key == pygame.K_KP1 or \
            event_key == pygame.K_KP2 or \
            event_key == pygame.K_KP3 or \
            event_key == pygame.K_KP4 or \
            event_key == pygame.K_KP5 or \
            event_key == pygame.K_KP6 or \
            event_key == pygame.K_KP7 or \
            event_key == pygame.K_KP8 or \
            event_key == pygame.K_KP9:
        return True

    return False


def constraint_allowed_values( event_key: str ) -> bool:
    """ Checking which values are allowed when inserting the constraints

    :param event_key:
    :type event_key:
    :return:
    :rtype:
    """

    return is_keyboard_number( event_key ) or \
           event_key == pygame.K_RETURN or \
           event_key == pygame.K_SPACE or \
           event_key == pygame.K_BACKSPACE


def sbra( event ):
    print( "Yey" )

