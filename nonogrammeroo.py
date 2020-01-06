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
# Description: Nonogram solver based on a cp solver
#


import argparse
from math import sqrt
from re import match

from ortools.sat.python import cp_model
from typing import Dict, List, Tuple


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
CELL_EMPTY = "_"
CELL_FULL = "O"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CLASSES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Cell:
    """ Implementation of a cell of the Nonogram

    :ivar _value: (bool) The cell is either full (True) or empty (False)
    """

    def __init__( self, value: bool = False ):
        self._value = value

    @property
    def value( self ) -> bool:
        return self._value


class Coordinates:
    """ Implementation of a cell coordinates inside the Nonogram table

    :ivar _x: (int) X-coordinate
    :ivar _y: (int) Y-coordinate
    """

    def __init__( self, x: int, y: int ):
        self._x = x
        self._y = y

    @property
    def x( self ) -> int:
        return self._x

    @property
    def y( self ) -> int:
        return self._y

    def __str__( self ):
        return "[{}, {}]".format( self.x, self.y )


class Region:
    """ Implementation of a line of cells

    .. note:: This class has been implemented in case regions with weird shapes are needed

    :ivar _region: (List[ Coordinates ]) Region of cells, will be used as either row or column
    :ivar _constraint: (List[ int ]) Constraint to be applied on the region
    """

    def __init__( self, indexes: List[ Coordinates ] ):
        self._region = indexes
        self._constraint = []

    @property
    def region( self ) -> List[ Coordinates ]:
        return self._region

    @property
    def constraint( self ) -> List[ int ]:
        return self._constraint

    @constraint.setter
    def constraint( self, constraint: List[ int ] ):
        self._constraint = constraint

    def is_row( self ) -> bool:
        """ Method used to check if the current region is a row

        :return: True if the current region is a row, False otherwise
        :rtype: bool
        """

        return [ point.x for point in self.region ].count( self.region[ 0 ].x ) == len( self.region )

    def is_column( self ) -> bool:
        """ Method used to check if the current region is a column

        :return: True if the current region is a column, False otherwise
        :rtype: bool
        """

        return [ point.y for point in self.region ].count( self.region[ 0 ].y ) == len( self.region )

    def __str__( self ):
        return "{} on {}".format( ",".join( [ str( el ) for el in self.constraint ] ),
                                  ",".join( [ str( point ) for point in self.region ] ) )


class NonogramBoard:
    """ Implementation of a Nonogram board

    :ivar _size: (int) Mono-dimensional size of the current board
    :ivar _board: (List[ List[ Cell ] ]) Current board size
    :ivar _regions: (List[ Region ]) List of constrained regions, i.e. rows and columns
    :ivar _solutions: (List[ List[ Tuple[ cp_model.IntVar, int ] ] ]): List of solutions found
    """

    def __init__( self, size: int = 10 ):
        self._size = size
        self._board = [ [ Cell() ] * size ] * size
        self._regions = []
        for i in range( size ):
            self.regions.append( Region( [ Coordinates( i, j ) for j in range( 0, size ) ] ) )
            self.regions.append( Region( [ Coordinates( j, i ) for j in range( 0, size ) ] ) )
        self._solutions = []

    @property
    def size( self ) -> int:
        return self._size

    @property
    def board( self ) -> List[ List[ Cell ] ]:
        return self._board

    @property
    def regions( self ) -> List[ Region ]:
        return self._regions

    @property
    def solutions( self ) -> List[ List[ Tuple[ cp_model.IntVar, int ] ] ]:
        return self._solutions

    @solutions.setter
    def solutions( self, solutions: List[ List[ Tuple[ cp_model.IntVar, int ] ] ] ):
        self._solutions = solutions

    def constraint_of( self, direction: str, index: int, constraint: List[ int ] ) -> None:
        """ Applying the constraint to a specific region of the table

        :param direction: Either "row" or "column"
        :type direction: str
        :param index: Index of the region on which the current constraint has to be applied
        :type index: int
        :param constraint: Constraint information
        :type constraint: List[ int ]
        :return: None
        :rtype: None

        :raises IndexError: error raised when the index is out of the board range
        """

        if index not in range( 0, self.size ):
            raise IndexError( "Index out of the game board: {}, boundaries [ 0, {} ]".format( index, self.size ) )

        if direction == "row":
            selected = [ region for region in self.regions if region.is_row() and region.region[ 0 ].x == index ]
        else:
            selected = [ region for region in self.regions if region.is_column() and region.region[ 0 ].y == index ]

        selected[ 0 ].constraint = constraint

    def solve( self ) -> None:
        """ Solving the current game instance as a constraint programming problem

        :return: None
        :rtype: None
        """

        # Creating the CP problem
        model = cp_model.CpModel()

        # Creating a variable for each cell of the table
        cp_cell = [ [] ] * self.size
        for row in range( self.size ):
            cp_cell[ row ] = [] * self.size
            for col in range( self.size ):
                cp_cell[ row ].append( model.NewBoolVar( "{}-{}".format( row, col ) ) )

        # Generating the constraints for each region
        cp_region = []
        for region in self.regions:
            if region.is_row():
                region_type = "r"
                region_index = region.region[ 0 ].x
                region_variables = cp_cell[ region_index ]
            else:
                region_type = "c"
                region_index = region.region[ 0 ].y
                region_variables = [ var[ region_index ] for var in cp_cell ]

            # Sum of the region must sum up to the region constraint
            model.Add( cp_model.LinearExpr.Sum( region_variables ) == sum( region.constraint ) )

            # Region variables and constraints
            # Space between sequences
            space_max = self.size - sum( region.constraint )
            # Leading space of the region
            space_variables = [ model.NewIntVar( 0, space_max, "{}{}-space_0".format( region_index, region_type ) ) ]

            # Handling each sequence of the constraint
            seq_variables = []
            seq_element = 0
            seq_cum = 0
            for seq_index, seq_length in enumerate( region.constraint, start=1 ):
                for i in range( seq_length ):
                    # Creating one variable for each element of the given constraint
                    seq_variables.append(
                            model.NewIntVar( 0,
                                             self.size,
                                             "{}{}-el_{}".format( region_index, region_type, seq_element ) ) )
                    # Each element of the sequence depends on the spaces and sequences before it
                    model.Add( seq_variables[ -1 ] == cp_model.LinearExpr.Sum( space_variables ) + seq_cum + i )
                    seq_element += 1
                seq_cum += seq_length

                # Creating a variable for the space following the current sequence
                # If the current sequence is the last of the board then the space might not exist
                # Setting at least one space between sequences inside the region
                min_space_domain = 0 if seq_index == len( region.constraint ) else 1
                space_variables.append( model.NewIntVar( min_space_domain,
                                                         max( 1, space_max ),
                                                         "{}{}-space_{}".format( region_index,
                                                                                 region_type,
                                                                                 seq_index ) ) )

            # Associating the element variables to the cells of the board
            for el_var in seq_variables:
                model.AddElement( el_var, region_variables, 1 )

            # Imposing a fixed value to the number of space in the board to obtain a unique solution
            model.Add( cp_model.LinearExpr.Sum( space_variables ) == space_max )

            # Saving all the variables created
            cp_region.extend( space_variables )
            cp_region.extend( seq_variables )

        # Solving the problem
        solver = cp_model.CpSolver()
        solutions = CpSolutionPrinter( { "cells": [ var for row in cp_cell for var in row ],
                                         "regions": cp_region } )
        status = solver.SearchForAllSolutions( model, solutions )
        #   print( "The problem is {}. {} solutions have been found.".format( solver.StatusName( status ),
        #                                                                     len( solutions ) ) )

        # Saving the solutions found
        self.solutions = solutions.solutions

    def print( self, data: List[ List[ Cell ] ] = None ) -> str:
        """ Printing the nonogram table on a formatted string

        :param data: Data of the board to use if a solution has been provided
        :type data: List[ List[ Cell ] ]
        :return: The formatted string
        :rtype: str
        """

        result = ""

        # If not data is provided, printing the empty board
        if data is None:
            data = self.board
            result = " *** Nonogram {}x{} board ***\n\n".format( self.size, self.size )

        # Fancy spaces for the constraints
        left_space = max( [ len( region.constraint ) for region in self.regions ] ) * 2
        table_space = len( str( max( [ max( region.constraint ) for region in self.regions if region.is_column() ] ) ) )

        # Column constraints
        max_constraint = max( [ len( region.constraint ) for region in self.regions if region.is_column() ] )
        for index in range( max_constraint ):
            result += "{msg:{space}} | ".format( msg="", space=left_space )
            for region in [ region for region in self.regions if region.is_column() ]:
                # Showing the column constraint starting closer to the board
                if len( region.constraint ) < max_constraint:
                    if max_constraint - index <= len( region.constraint ):
                        #   msg = region.constraint[ max_constraint - index - 1 ]
                        msg = region.constraint[ abs( max_constraint - len( region.constraint ) - index ) ]
                    else:
                        msg = " "
                else:
                    msg = region.constraint[ index ]
                result += "{msg:{table_space}} ".format( msg=msg, table_space=table_space )
            result += "\n"

        # Divider
        result += "{}\n".format( "-" * ( left_space + self.size * ( table_space + 1 ) + 3 ) )

        # Row constraints and table cells
        row_index = 0
        for region in self.regions:
            if region.is_row():
                result += "{constraint:>{space}} | {row}".format(
                            constraint=" ".join( [ str( el ) for el in region.constraint ] ),
                            space=left_space,
                            row=" ".join( [ "{msg:>{space}}".format( msg=CELL_FULL if el.value else CELL_EMPTY,
                                                                     space=table_space )
                                            for el in data[ row_index ] ] ),
                            table_space=table_space )
                row_index += 1
                result += "\n"

                #   if row_index % 5 == 0:
                #       result += "{msg:{left_space}} | {table}\n".format(
                #               msg="",
                #               left_space=left_space,
                #               table="-" * ( ( self.size + int( self.size / 5 ) ) * 2 * table_space ) )

        return result

    def print_solutions( self ) -> str:
        """ Printing all the solutions found

        :return: A formatted string with all the solutions found
        :rtype: str

        :raises ValueError: error raised when the function is called before the board has been solved
        """

        if self.solutions is None:
            raise ValueError( "No solutions have been found yet!" )

        # Composing the formatted string with all the solutions found
        result = ""
        for index, solution in enumerate( self.solutions, start=1 ):
            result += " === Solution {} ===\n\n".format( index )
            # Recomposing the nonogram board from the solutions found
            solution_data = []
            for i in range( self.size ):
                solution_data.append( [ Cell( bool( cell_value[ 1 ] ) ) for cell_value in solution
                                        if match( r"\d+-\d+", cell_value[ 0 ].Name() ) and
                                        int( cell_value[ 0 ].Name().split( "-" )[ 0 ] ) == i ] )

            result += self.print( solution_data )

        return result


class CpSolutionPrinter( cp_model.CpSolverSolutionCallback ):
    """ CP Solution Printer used each time a solution is found


    :ivar _cell_variables: (List[ cp_model.IntVar ]) CP variables of the cell composing the Nonogram board
    :ivar _region_variables: (List[ cp_model.IntVar ]) CP variables of the regions of the Nonogram board
    :ivar _solutions: (List[ List[ Tuple[ cp_model.IntVar, int ] ] ]) List of solutions found stored as tuples
    """

    def __init__( self, variables: Dict[ str, List[ cp_model.IntVar ] ] ):
        cp_model.CpSolverSolutionCallback.__init__( self )
        self._cell_variables = variables[ "cells" ]
        self._region_variables = variables[ "regions" ]
        self._solutions = []

    @property
    def variables( self ) -> List[ cp_model.IntVar ]:
        return self._cell_variables + self._region_variables

    @property
    def cell_variables( self ) -> List[ cp_model.IntVar ]:
        return self._cell_variables

    @property
    def region_variables( self ) -> List[ cp_model.IntVar ]:
        return self._region_variables

    @property
    def solutions( self ) -> List:
        return self._solutions

    def __len__( self ):
        return len( self.solutions )

    def on_solution_callback( self ) -> None:
        """ Method invoked when a solution is found

        :return: None
        :rtype: None
        """

        self.solutions.append( [ ( var, self.Value( var ) ) for var in self.variables ] )

        # More detailed information of all the variables of the cp problem
        #   for index in range( int( math.sqrt( len( self.cell_variables ) ) ) ):
        #       var_row = [ var for var in self.cell_variables if int( var.Name().split( "-" )[ 0 ] ) == index ]
        #       print( " ".join( [ str( self.Value( el ) ) for el in var_row ] ) )

        #   print( "-" * 32 )

        #   for var in self.region_variables:
        #       print( "{}: {}".format( var.Name(), self.Value( var ) ) )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


def main():
    # region Command Line arguments
    # Reading arguments from command line
    arg_parser = argparse.ArgumentParser( description="<description>" )
    arg_parser.add_argument( "--save", dest="save", default=False, action="store_true",
                             help="Flag to indicate if the results have to be saved on file or not" )

    input_args = vars( arg_parser.parse_args() )
    # endregion

    for sbra in [ 5, 10, 15 ]:
        if sbra == 25:
            # Board #510 of paper "Nonogram Tournaments in TAAI 2011", Sun et Al, ICGA Journal, June 2012
            # The algorithm used is not optimized to solve this board in short time
            nonogram = NonogramBoard( 25 )
            # Rows
            nonogram.constraint_of( "row", 0, [ 1, 2, 2, 2, 1, 1 ] )
            nonogram.constraint_of( "row", 1, [ 1, 1, 1, 3, 2, 1, 2 ] )
            nonogram.constraint_of( "row", 2, [ 1, 2, 1, 1, 1, 2, 1, 1 ] )
            nonogram.constraint_of( "row", 3, [ 1, 1, 2, 1, 2, 1 ] )
            nonogram.constraint_of( "row", 4, [ 1, 4, 1, 1, 1, 1 ] )
            nonogram.constraint_of( "row", 5, [ 1, 2, 1, 1, 3, 3 ] )
            nonogram.constraint_of( "row", 6, [ 2, 1, 1, 1, 2, 2, 2, 3 ] )
            nonogram.constraint_of( "row", 7, [ 1, 1, 1, 6, 1, 2 ] )
            nonogram.constraint_of( "row", 8, [ 2, 5, 2, 2 ] )
            nonogram.constraint_of( "row", 9, [ 1, 1, 2, 1, 2, 1, 1 ] )
            nonogram.constraint_of( "row", 10, [ 1, 2, 1, 2, 3, 1 ] )
            nonogram.constraint_of( "row", 11, [ 4, 1, 3, 2 ] )
            nonogram.constraint_of( "row", 12, [ 1, 2, 2, 4, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "row", 13, [ 1, 1, 1, 4, 3, 1, 1 ] )
            nonogram.constraint_of( "row", 14, [ 1, 2, 1, 1, 3, 2, 1, 1 ] )
            nonogram.constraint_of( "row", 15, [ 2, 1, 3, 2 ] )
            nonogram.constraint_of( "row", 16, [ 1, 5, 1, 1, 1, 1, 1 ] )
            nonogram.constraint_of( "row", 17, [ 1, 1, 3, 1, 2, 2 ] )
            nonogram.constraint_of( "row", 18, [ 2, 1, 2, 2, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "row", 19, [ 1, 4, 1, 1, 1, 2, 1, 1 ] )
            nonogram.constraint_of( "row", 20, [ 1, 1, 1, 1, 2, 1, 1, 1 ] )
            nonogram.constraint_of( "row", 21, [ 1, 3, 2, 1, 1, 2, 1 ] )
            nonogram.constraint_of( "row", 22, [ 2, 2, 2, 2, 1, 3 ] )
            nonogram.constraint_of( "row", 23, [ 3, 1, 1, 1, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "row", 24, [ 3, 1, 1, 1 ] )
            # Columns
            nonogram.constraint_of( "column", 0, [ 5, 2, 1, 1, 3 ] )
            nonogram.constraint_of( "column", 1, [ 2, 1, 1, 1, 1, 3 ] )
            nonogram.constraint_of( "column", 2, [ 4, 1, 1, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "column", 3, [ 1, 1, 2, 1, 5, 1, 1 ] )
            nonogram.constraint_of( "column", 4, [ 1, 3, 3, 1, 2, 1 ] )
            nonogram.constraint_of( "column", 5, [ 1, 1, 1, 3, 1, 1, 1 ] )
            nonogram.constraint_of( "column", 6, [ 1, 1, 1, 1, 1, 2, 1 ] )
            nonogram.constraint_of( "column", 7, [ 1, 1, 2, 3, 1, 1, 1 ] )
            nonogram.constraint_of( "column", 8, [ 1, 6, 2, 4 ] )
            nonogram.constraint_of( "column", 9, [ 1, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "column", 10, [ 2, 1, 2, 2, 1, 2, 1 ] )
            nonogram.constraint_of( "column", 11, [ 1, 2, 3, 3, 1, 2 ] )
            nonogram.constraint_of( "column", 12, [ 2, 4, 9, 2 ] )
            nonogram.constraint_of( "column", 13, [ 2, 1, 3, 3, 1 ] )
            nonogram.constraint_of( "column", 14, [ 2, 4, 1, 1, 1, 1, 2, 1 ] )
            nonogram.constraint_of( "column", 15, [ 1, 1, 2, 3, 3, 1, 1 ] )
            nonogram.constraint_of( "column", 16, [ 1, 1, 1, 2, 2, 1, 1, 1 ] )
            nonogram.constraint_of( "column", 17, [ 1, 1, 2, 2, 1, 2, 4, 1 ] )
            nonogram.constraint_of( "column", 18, [ 1, 2, 2, 1, 2, 2 ] )
            nonogram.constraint_of( "column", 19, [ 1, 2, 2, 1, 1 ] )
            nonogram.constraint_of( "column", 20, [ 4, 1, 1, 1, 1, 2 ] )
            nonogram.constraint_of( "column", 21, [ 1, 1, 1, 1, 1, 2, 2, 1, 1, 1 ] )
            nonogram.constraint_of( "column", 22, [ 1, 1, 2, 1, 2 ] )
            nonogram.constraint_of( "column", 23, [ 1, 1, 2, 3, 1, 1, 2 ] )
            nonogram.constraint_of( "column", 24, [ 1, 1, 1, 2, 1, 1 ] )
        elif sbra == 15:
            nonogram = NonogramBoard( 15 )
            # Rows
            nonogram.constraint_of( "row", 0, [ 1 ] )
            nonogram.constraint_of( "row", 1, [ 1 ] )
            nonogram.constraint_of( "row", 2, [ 3 ] )
            nonogram.constraint_of( "row", 3, [ 5 ] )
            nonogram.constraint_of( "row", 4, [ 2, 2 ] )
            nonogram.constraint_of( "row", 5, [ 10 ] )
            nonogram.constraint_of( "row", 6, [ 4, 3 ] )
            nonogram.constraint_of( "row", 7, [ 3, 1, 3 ] )
            nonogram.constraint_of( "row", 8, [ 5, 3, 4 ] )
            nonogram.constraint_of( "row", 9, [ 3, 3, 4, 1 ] )
            nonogram.constraint_of( "row", 10, [ 4, 8 ] )
            nonogram.constraint_of( "row", 11, [ 2, 2, 3, 1, 2 ] )
            nonogram.constraint_of( "row", 12, [ 2, 3, 4 ] )
            nonogram.constraint_of( "row", 13, [ 1, 2, 2 ] )
            nonogram.constraint_of( "row", 14, [ 2 ] )
            # Columns
            nonogram.constraint_of( "column", 0, [ 7 ] )
            nonogram.constraint_of( "column", 1, [ 6, 1 ] )
            nonogram.constraint_of( "column", 2, [ 5 ] )
            nonogram.constraint_of( "column", 3, [ 4, 2 ] )
            nonogram.constraint_of( "column", 4, [ 2, 2, 3 ] )
            nonogram.constraint_of( "column", 5, [ 3, 1, 2 ] )
            nonogram.constraint_of( "column", 6, [ 3, 2, 2 ] )
            nonogram.constraint_of( "column", 7, [ 2, 1, 2, 2 ] )
            nonogram.constraint_of( "column", 8, [ 4, 1, 5 ] )
            nonogram.constraint_of( "column", 9, [ 2, 1, 2, 2 ] )
            nonogram.constraint_of( "column", 10, [ 3, 2, 2 ] )
            nonogram.constraint_of( "column", 11, [ 3, 5 ] )
            nonogram.constraint_of( "column", 12, [ 4, 1 ] )
            nonogram.constraint_of( "column", 13, [ 3, 2 ] )
            nonogram.constraint_of( "column", 14, [ 5 ] )
        elif sbra == 10:
            nonogram = NonogramBoard( 10 )
            # Rows
            nonogram.constraint_of( "row", 0, [ 4 ] )
            nonogram.constraint_of( "row", 1, [ 2, 2 ] )
            nonogram.constraint_of( "row", 2, [ 2, 2 ] )
            nonogram.constraint_of( "row", 3, [ 2, 2 ] )
            nonogram.constraint_of( "row", 4, [ 2, 2 ] )
            nonogram.constraint_of( "row", 5, [ 2, 2 ] )
            nonogram.constraint_of( "row", 6, [ 4 ] )
            nonogram.constraint_of( "row", 7, [ 6 ] )
            nonogram.constraint_of( "row", 8, [ 8 ] )
            nonogram.constraint_of( "row", 9, [ 10 ] )
            # Columns
            nonogram.constraint_of( "column", 0, [ 1 ] )
            nonogram.constraint_of( "column", 1, [ 3, 2 ] )
            nonogram.constraint_of( "column", 2, [ 5, 3 ] )
            nonogram.constraint_of( "column", 3, [ 2, 5 ] )
            nonogram.constraint_of( "column", 4, [ 1, 4 ] )
            nonogram.constraint_of( "column", 5, [ 1, 4 ] )
            nonogram.constraint_of( "column", 6, [ 2, 5 ] )
            nonogram.constraint_of( "column", 7, [ 5, 3 ] )
            nonogram.constraint_of( "column", 8, [ 3, 2 ] )
            nonogram.constraint_of( "column", 9, [ 1 ] )
        else:
            nonogram = NonogramBoard( 5 )
            # Rows
            nonogram.constraint_of( "row", 0, [ 1 ] )
            nonogram.constraint_of( "row", 1, [ 1, 2 ] )
            nonogram.constraint_of( "row", 2, [ 3, 1 ] )
            nonogram.constraint_of( "row", 3, [ 5 ] )
            nonogram.constraint_of( "row", 4, [ 5 ] )
            # Columns
            nonogram.constraint_of( "column", 0, [ 4 ] )
            nonogram.constraint_of( "column", 1, [ 1, 3 ] )
            nonogram.constraint_of( "column", 2, [ 4 ] )
            nonogram.constraint_of( "column", 3, [ 1, 2 ] )
            nonogram.constraint_of( "column", 4, [ 3 ] )

        # Dividing from the previous boards
        print( "_" * 50, end="\n\n" )
        # Printing the board with the constraints
        print( nonogram.print() )
        # Solve
        nonogram.solve()
        # Printing the solutions found
        print( nonogram.print_solutions() )

    print( "DONE (•̀o•́)ง" )


if __name__ == "__main__":
    main()
