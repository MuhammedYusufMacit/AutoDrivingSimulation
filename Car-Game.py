from win32api import GetSystemMetrics

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import math
import random
import sys
import os

import neat
import pygame

#Monitor Resolutions
RESOLUTION_X=GetSystemMetrics(0)
RESOLUTION_Y=GetSystemMetrics(1)

size_of_car = 60    

drawradar=0
current = 0 # Gen counter
Game_Settings="settings.txt"

def run(gnr, setting):

    nets = []
    cars = []

    pygame.init()
    screen = pygame.display.set_mode((RESOLUTION_X, RESOLUTION_Y), pygame.FULLSCREEN)

    for i, g in gnr:
        net = neat.nn.FeedForwardNetwork.create(g, setting)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    clk = pygame.time.Clock()
    font_1 = pygame.font.SysFont("Times New Roman", 48)
    font_2 = pygame.font.SysFont("Times New Roman", 32)
    map = pygame.image.load('drawing.png').convert() 

    global current
    current += 1

    counter = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                sys.exit(0)
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10
            elif choice == 1:
                car.angle -= 10
            elif choice == 2:
                if(car.speed - 2 >= 12):
                    car.speed -= 2
            else:
                car.speed += 2
        
        car_count = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                car_count += 1
                car.update_game(map)
                gnr[i][1].fitness += car.get_reward()

        if car_count == 0:
            break

        counter += 1
        if counter == 30 * 40:
            break

        screen.blit(map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        current_color=(10*current%128,60*current%255,60*current%255)
        if car_count < 5:
            car_count_color=(255,0,0)
        elif car_count < 12:
            car_count_color=(0,0,255)
        else:
            car_count_color=(0,255,0)
            
        text = font_1.render("GEN: " + str(current), True, current_color)
        text_rect = text.get_rect()
        text_rect.center = (RESOLUTION_X/2, 50)
        screen.blit(text, text_rect)
        
    
        text = font_2.render("CAR: " + str(car_count), True, car_count_color)
        text_rect = text.get_rect()
        text_rect.center = (RESOLUTION_X/2, 100)
        screen.blit(text, text_rect)
        
        text = font_2.render("Press Q for Quit.", True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.center = (RESOLUTION_X-150, 20)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clk.tick(60)

def drawimg_app():
    drawimg_app = QApplication(sys.argv)
    window = Window()
    window.show()
    drawimg_app.exec()

    return 0

class Car:
    
    def __init__(self):
        self.sprite = pygame.image.load('car.png').convert()
        self.sprite = pygame.transform.scale(self.sprite, (size_of_car, size_of_car))
        self.rotated_sprite = self.sprite
        self.speed_set = False
        self.angle, self.distance, self.time, self.speed = 0, 0, 0, 0
        self.pos = [960, 200]
        self.center = [self.pos[0] + size_of_car / 2, self.pos[1] + size_of_car / 2]
        self.radars = [] 
        self.drawing_radars = []
        self.alive = True

    
    def update_game(self, map):
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        self.rotated_sprite = self.center_rotate(self.sprite, self.angle)
        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.pos[0] = max(self.pos[0], 20)
        self.pos[0] = min(self.pos[0], RESOLUTION_X - 120)

        self.distance += self.speed
        self.time += 1

        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.pos[1] = max(self.pos[1], 20)
        self.pos[1] = min(self.pos[1], RESOLUTION_X - 120)

        self.center = [int(self.pos[0]) + size_of_car / 2, int(self.pos[1]) + size_of_car / 2]

        length = 0.5 * size_of_car
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        self.collision(map)
        self.radars.clear()

        for d in range(-90, 120, 45):
            self.check(d, map)
    
    def check(self, degree, map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        while not map.get_at((x, y)) == (255, 255, 255, 255) and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
        
    def center_rotate(self, image, angle):
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image

    def get_data(self):
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values
    
    def collision(self, map):
        self.alive = True
        for point in self.corners:
            if map.get_at((int(point[0]), int(point[1]))) == (255, 255, 255, 255):
                self.alive = False
                break
            
    def draw_radar(self, screen):
        for radar in self.radars:
            pos = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, pos, 1)
            pygame.draw.circle(screen, (0, 255, 0), pos, 5)
            
    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.pos)
        if(drawradar):
            self.draw_radar(screen)

    def is_alive(self):
        return self.alive

    def get_reward(self):
        return self.distance / (size_of_car / 2)



# window class
class Window(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Draw a Map!")

		# Main Window resolution
		self.setGeometry(100, 100, RESOLUTION_X, RESOLUTION_Y)

		self.image = QImage(self.size(), QImage.Format_RGB32)
		self.image.fill(Qt.white)

		# variables
		self.drawing = False
		# default brush size
		self.brushSize = 72
		# default color
		self.brushColor = Qt.black

		self.lastPoint = QPoint()

		# creating menu bar
		mainMenu = self.menuBar()

		fileMenu = mainMenu.addMenu("Save-Clear")
		b_size = mainMenu.addMenu("Size")
		b_color = mainMenu.addMenu("Color")


		saveAction = QAction("Save", self)
		saveAction.setShortcut("Ctrl + S")
		fileMenu.addAction(saveAction)
		saveAction.triggered.connect(self.save)

		clearAction = QAction("Clear", self)
		clearAction.setShortcut("Ctrl + C")
		fileMenu.addAction(clearAction)
		clearAction.triggered.connect(self.clear)

		# creating options for brush sizes
		pix_48 = QAction("48px", self)
		b_size.addAction(pix_48)
		pix_48.triggered.connect(self.Pixel_48)
        
		pix_72 = QAction("72px", self)
		b_size.addAction(pix_72)
		pix_72.triggered.connect(self.Pixel_72)

		pix_96 = QAction("96px", self)
		b_size.addAction(pix_96)
		pix_96.triggered.connect(self.Pixel_96)

		pix_128 = QAction("128px", self)
		b_size.addAction(pix_128)
		pix_128.triggered.connect(self.Pixel_128)

		# creating options for brush color
		black = QAction("Black", self)
		b_color.addAction(black)
		black.triggered.connect(self.blackColor)
        
		white = QAction("White", self)
		b_color.addAction(white)
		white.triggered.connect(self.whiteColor)


	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.drawing = True
			self.lastPoint = event.pos()
            
	def mouseMoveEvent(self, event):
		if (event.buttons() & Qt.LeftButton) & self.drawing:
			painter = QPainter(self.image)
			painter.setPen(QPen(self.brushColor, self.brushSize,
							Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
			painter.drawLine(self.lastPoint, event.pos())
            
			self.lastPoint = event.pos()
			self.update()

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.drawing = False

	# paint event
	def paintEvent(self, event):
		canvasPainter = QPainter(self)
		canvasPainter.drawImage(self.rect(), self.image, self.image.rect())

	def save(self):
		filePath, _ = QFileDialog.getSaveFileName(self, "Save Image", "drawing",
						"PNG(*.png);")

		if filePath == "":
			return
		self.image.save(filePath)

	# method for clearing every thing on canvas
	def clear(self):
		self.image.fill(Qt.white)
		self.update()


	def Pixel_48(self):
		self.brushSize = 48

	def Pixel_72(self):
		self.brushSize = 72

	def Pixel_96(self):
		self.brushSize = 96

	def Pixel_128(self):
		self.brushSize = 128

	def blackColor(self):
		self.brushColor = Qt.black

	def whiteColor(self):
		self.brushColor = Qt.white






if __name__ == "__main__":
    print("Width =", GetSystemMetrics(0))
    print("Height =", GetSystemMetrics(1))
         
    settings = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                Game_Settings)

    drawimg_app()

    population = neat.Population(settings)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    population.run(run, 1000)
