import PIL.ImageOps
import Image #Help: http://effbot.org/imagingbook/introduction.htm
import os
from osgeo import osr
from osgeo import gdal
import mapnik
import numpy as np

import googleProj as proj

class TileMos:
	def __init__(self, out_file, tiles_folder):
		self.out = open(out_file,'w')
		self.tiles_folder = tiles_folder

	def writeToOutfile(self, content):
		self.out.write(content)

	def closeWriting(self):
		self.out.close()

	def renderImage(self, map_output, mapfile, imgx, imgy):
		print "renderImage"
		m = mapnik.Map(imgx, imgy)
		mapnik.load_map(m, mapfile)
		#ll = (1321613.269848, 6475998.706584, 1674460.199655, 6743324.6719772)
		ll = (1321613.269848, 6475998.706584, 1674460.199655, 6743324.671977)
		bbox = mapnik.Box2d(mapnik.Coord(ll[0], ll[3]), mapnik.Coord(ll[2], ll[1]))
		m.zoom_to_box(bbox)
		mapnik.render_to_file(m, map_output)

	def getNumberOfTiles(self, zoom):
		return self.calculateNecTiles(zoom, zoom, False)

	def setExtent(self, minll, maxll):
		self.minll = minll
		self.maxll = maxll

	def deleteTileFolder(self, folder):
		command = "rm -rf %s"%folder
		os.system(command)

	def readPixelsFromImage(self, fileName):
		print "readPixelsFromImage"
		self.writeToOutfile("open: "+ fileName)
		im = Image.open(fileName)

		#print im.format, im.size, im.mode
		width=  im.size[0]
		heigth = im.size[1]

		content = im.getdata()
		lineValues = []
		for line in xrange (heigth):
			singleValues = []
			for i in range((width*line),(((width*line)+width)-1)+1):
				singleValues.append(content[i])
			lineValues.append(singleValues)
		#im.show()

		return lineValues
	
	def getCoordinatesFromTiff(self, image): #Help: http://stackoverflow.com/questions/2922532/obtain-latitude-and-longitude-from-a-geotiff-file
		print "getCoordinatesFromTiff"
		ds = gdal.Open(image)
		width = ds.RasterXSize
		height = ds.RasterYSize
		gt = ds.GetGeoTransform()
		minx = gt[0]
		miny = gt[3] + width*gt[4] + height*gt[5] 
		maxx = gt[0] + width*gt[1] + height*gt[2]
		maxy = gt[3] 
		coordinates = []
		coordinates.append(minx)
		coordinates.append(miny)
		coordinates.append(maxx)
		coordinates.append(maxy)

		self.writeToOutfile("\nMinX: " + str(minx))
		self.writeToOutfile("\nMaxX: " + str(maxx))
		self.writeToOutfile("\nMinY: " + str(miny))
		self.writeToOutfile("\nMaxY: " + str(maxy))

		# get the existing coordinate system
		old_cs= osr.SpatialReference()
		old_cs.ImportFromWkt(ds.GetProjectionRef())
		self.writeToOutfile("\nProjection: \n"+str(old_cs))

		return old_cs, coordinates
		

	def calculateNecTiles(self, minZoom, maxZoom, write):
		tileproj = proj.GoogleProjection(19+1)
		dpi = 300
		tileSizePrinted = (256*2.54)/dpi #1inch = 2,54cm
		if write == True:
			self.writeToOutfile("\n********")
			self.writeToOutfile("\nPrint resolution: "+str(dpi))
			self.writeToOutfile("\nPrinted tile size: %s cm"%str(tileSizePrinted))
			self.writeToOutfile("\n********")
		for z in range(minZoom,maxZoom+1):
			zoomlevel = z
			pxMin = tileproj.fromLLtoPixel((self.minll[0],self.minll[1]),zoomlevel)
			pxMax = tileproj.fromLLtoPixel((self.maxll[0],self.maxll[1]),zoomlevel)
			#print pxMin, pxMax
			 
			pxWidth = pxMax[0]-pxMin[0]
			pxLength = pxMin[1]-pxMax[1]
			
			self.tilesX = []
			counter = 0
			for x in range(int(pxMin[0]/256.0),int(pxMax[0]/256.0)+1):
		   	 	self.tilesX.append(x)
				counter = counter + 1
			self.tilesY = []
			pixelsX = counter
			counter = 0
			for x in range(int(pxMax[1]/256.0),int(pxMin[1]/256.0)+1):
		   	 	self.tilesY.append(x)
				counter = counter + 1
			pixelsY = counter
			if write == True:
				self.writeTileDebug(pxMin, pxMax, zoomlevel, pxWidth, pxLength, tileSizePrinted, pixelsX, pixelsY)
			

		return pixelsX, pixelsY

	def transformCoordinates(self, old_cs, coordinates):
		# create the new coordinate system
		proj84 = proj.GeoProj()
		wgs84_wkt = proj84.getWGS84wkt()
		new_cs = osr.SpatialReference()
		new_cs .ImportFromWkt(wgs84_wkt)
		# create a transform object to convert between coordinate systems
		transform = osr.CoordinateTransformation(old_cs,new_cs) 

		#get the coordinates in lat long
		minll = transform.TransformPoint(coordinates[0],coordinates[1]) 
		maxll = transform.TransformPoint(coordinates[2],coordinates[3]) 
		self.writeToOutfile("\nTransformed Coords: \n" + str(minll) +"\n"+str(maxll))
		return minll, maxll

	def loadTiles(self, zoom, url):
		print "loadTiles"
		self.calculateNecTiles(zoom, zoom, False)
		z = zoom
		line_counter = 0
		for y in self.tilesY:
			pixel_counter = 0
			for x in self.tilesX:
				request = "wget %s/%s/%s/%s.png -P %s/%s/%s"%(url,z,x,y,self.tiles_folder,z,x)
				#request = "wget %s/%s/%s/%s.png -P %s -O %s-%s-%s.png"%(url,z,x,y,self.tiles_folder,z,x,y)
				#print request
				os.system(request)
				pixel_counter = pixel_counter + 1
			line_counter = line_counter + 1

	def changeTiles(self, zoom, pixelValues, mode):
		print "changeTiles"
		self.calculateNecTiles(zoom, zoom, True)
		z = zoom
		line_counter = 0
		for y in self.tilesY:
			pixel_counter = 0
			for x in self.tilesX:
			  if mode == "BW":
				if pixelValues[line_counter][pixel_counter][0] != 255:
					tile = Image.open("%s/%s/%s/%s.png"%(self.tiles_folder,z,x,y))
					tile.load()
					tile = tile.convert('RGB')
					tile = PIL.ImageOps.invert(tile)
					tile.save("%s/%s/%s/%s.png"%(self.tiles_folder,z,x,y))
			  elif mode == "RGB":
				#print pixelValues[line_counter][pixel_counter]
				orig_color = (255,255,255)
				replacement_color = (pixelValues[line_counter][pixel_counter][0],pixelValues[line_counter][pixel_counter][1],pixelValues[line_counter][pixel_counter][2])
				if orig_color != replacement_color:# and line_counter == 54 and pixel_counter == 10:
					#print line_counter, pixel_counter
					#print replacement_color
					img = Image.open("%s/%s/%s/%s.png"%(self.tiles_folder,z,x,y)).convert('RGB')
					data = np.array(img)
				 	data[(data == orig_color).all(axis = -1)] = replacement_color
					img2 = Image.fromarray(data, mode = 'RGB')
					#img2.show()
					img2.save("%s/%s/%s/%s.png"%(self.tiles_folder,z,x,y))
					
			  pixel_counter = pixel_counter + 1
			line_counter = line_counter + 1


	def makeCombImage(self, zoom, print_resolution, combined_image):
		print "makeCombinedImage"
		self.calculateNecTiles(zoom, zoom, False)
		z = zoom
		self.new_im = Image.new('RGB', (len(self.tilesX*256),len(self.tilesY*256)))
		line_counter = 0
		for y in self.tilesY:
			pixel_counter = 0
			for x in self.tilesX:
				tile = Image.open("%s/%s/%s/%s.png"%(self.tiles_folder,z,x,y))
				self.new_im.paste(tile,(pixel_counter*256,line_counter*256))
				pixel_counter = pixel_counter + 1
			line_counter = line_counter + 1
		self.new_im.save(combined_image, dpi = print_resolution) #image.info["dpi"]

	def writeTileDebug(self, pxMin, pxMax, zoomlevel, pxWidth, pxLength, tileSizePrinted, pixelsX, pixelsY):
		self.writeToOutfile("\n###########")
		self.writeToOutfile("\nTile Pixel Coords: \n" + str(pxMin) +"\n"+str(pxMax))
		self.writeToOutfile("\nZoomlevel: "+str(zoomlevel))
		self.writeToOutfile("\nPixel width "+str(pxWidth))
		self.writeToOutfile("\nThat makes %s tiles"%str(pxWidth/256))
		self.writeToOutfile("\nThat makes a map size of %s cm"%str((pxWidth/256)*tileSizePrinted))
		self.writeToOutfile("\nPixel length "+str(pxLength))
		self.writeToOutfile("\nThat makes %s tiles"%str(pxLength/256))
		self.writeToOutfile("\nThat makes a map size of %s cm"%str((pxLength/256)*tileSizePrinted))
		self.writeToOutfile("\nTileNumber:\n%s"%pixelsX)
		self.writeToOutfile("\nTileNumber:\n%s"%pixelsY)
	 	self.writeToOutfile("\nTotal Tile Number: %s"%(pixelsX*pixelsY))
