#  Copyright 2020 Alexander Tait <atait@ieee.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
from kicad import pcbnew_bare as pcbnew

import kicad
from kicad.pcbnew import layer as pcbnew_layer
from kicad.point import Point
from kicad import units, SWIGtype, SWIG_version
from kicad.pcbnew.item import HasConnection, HasLayerStrImpl, Selectable
from kicad.pcbnew.layer import LayerSet

class KeepoutAllowance(object):
    """ Gives key-value interface of the form
            my_zone.is_keepout = True
            my_zone.allow['tracks'] = False
    """
    def __init__(self, zone):
        self._zone = zone

    def __getitem__(self, item):
        # if not self._zone.is_keepout:
        #     print('Warning: '
        #         'Keepout settings do not apply to fill zones.'
        #         ' Call "my_zone.is_keepout = True" first.'
        #     )
        if item == 'tracks':
            return not self._zone._obj.GetDoNotAllowTracks()
        elif item == 'pour':
            return not self._zone._obj.GetDoNotAllowCopperPour()
        elif item == 'vias':
            return not self._zone._obj.GetDoNotAllowVias()
        else:
            raise KeyError(
                'Invalid zone keepout allowance type: {}. '
                'Allowed types are "tracks, pour, vias"'.format(item)
            )

    def __setitem__(self, item, value):
        # if not self._zone.is_keepout:
        #     print('Warning: '
        #         'Keepout settings do not apply to fill zones.'
        #         ' Call "my_zone.is_keepout = True" first.'
        #     )
        if item == 'tracks':
            self._zone._obj.SetDoNotAllowTracks(not bool(value))
        elif item == 'pour':
            self._zone._obj.SetDoNotAllowCopperPour(not bool(value))
        elif item == 'vias':
            self._zone._obj.SetDoNotAllowVias(not bool(value))
        else:
            raise KeyError(
                'Invalid zone keepout allowance type: {}. '
                'Allowed types are "tracks, pour, vias"'.format(item)
            )

    def __str__(self):
        return str({k: self[k] for k in ['tracks', 'pour', 'vias']})

    def __repr__(self):
        return type(self).__name__ + str(self)


class Zone(HasConnection, HasLayerStrImpl, Selectable):
    def __init__(self, layer='F.Cu', board=None):
        self._obj = SWIGtype.Zone(board and board.native_obj)
        self.layer = layer
        raise NotImplementedError('Constructor not supported yet')

    @property
    def native_obj(self):
        return self._obj

    @staticmethod
    def wrap(instance):
        """Wraps a C++ api TRACK object, and returns a `Track`."""
        return kicad.new(Zone, instance)

    @property
    def clearance(self):
        return float(self._obj.GetClearance()) / units.DEFAULT_UNIT_IUS

    @clearance.setter
    def clearance(self, value):
        self._obj.SetClearance(int(value * units.DEFAULT_UNIT_IUS))
        self._obj.SetZoneClearance(int(value * units.DEFAULT_UNIT_IUS))

    @property
    def min_width(self):
        return float(self._obj.GetMinThickness()) / units.DEFAULT_UNIT_IUS

    @min_width.setter
    def min_width(self, value):
        self._obj.SetMinThickness(int(value * units.DEFAULT_UNIT_IUS))

    @property
    def is_keepout(self):
        if SWIG_version >= 6:
            return bool(self._obj.GetIsRuleArea())
        else:
            return bool(self._obj.GetIsKeepout())

    @is_keepout.setter
    def is_keepout(self, value):
        if SWIG_version >= 6:
            self._obj.SetIsRuleArea(bool(value))
        else:
            self._obj.SetIsKeepout(bool(value))

    @property
    def allow(self):
        return KeepoutAllowance(self)

    def delete(self):
        self._obj.DeleteStructure()

    @property
    def layerset(self):
        ''' For zones with multiple layers
            Changing this layerset will not propagate back to this zone
            until you set layerset again. Common pattern:
                zone.layerset = zone.layerset.add_layer('F.Cu')
        '''
        from kicad.pcbnew.board import Board
        layers_native = self._obj.GetLayerSet()
        lset = LayerSet.wrap(layers_native)
        lset._board = Board.wrap(self._obj.GetBoard())
        return lset

    @layerset.setter
    def layerset(self, new_lset):
        self._obj.SetLayerSet(new_lset._obj)

# GetCornerSmoothingType
# GetDefaultHatchPitch

# GetThermalReliefCopperBridge
# GetThermalReliefGap

# Outline
# RawPolysList
