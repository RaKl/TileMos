#!/usr/bin/env python

import os
from TileMos import tilemos

data_folder = "./data/"

tiles_folder = "./tiles"
debug_out = data_folder+"infos.txt"
mosaik = tilemos.TileMos(debug_out, tiles_folder)

image = 'saxony_shade_goog-cut-box.tif'
image_cs, image_coordinates = mosaik.getCoordinatesFromTiff(image)
minll, maxll = mosaik.transformCoordinates(image_cs, image_coordinates)
mosaik.setExtent(minll, maxll)

#mosaik.calculateNecTiles(5, 19, True)

zoom = 11
im = data_folder+"image_%s.png"%str(zoom)
mapfile = './styles/style_border.xml'
#im = data_folder+"rgb_image_%s.png"%str(zoom)
#mapfile = './styles/style.xml'
x,y = mosaik.getNumberOfTiles(zoom)
mosaik.renderImage(im, mapfile, x, y)
lineValues = mosaik.readPixelsFromImage(im)

#mosaik.deleteTileFolder(tiles_folder+"/"+str(zoom))
url = "http://b.tile.stamen.com/toner"
#mosaik.loadTiles(zoom, url)

mode = "BW"
mosaik.changeTiles(zoom, lineValues, mode)

combined_image = data_folder+"comb_image_%s_rgb.png"%str(zoom)
print_resolution = (300, 300)
#mosaik.makeCombImage(zoom, print_resolution, combined_image)

mosaik.closeWriting()
