#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = "1.0"

import kivy
kivy.require('1.8.0') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.carousel import Carousel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.actionbar import *
from kivy.clock import Clock
from kivy.loader import Loader
from kivy.uix.progressbar import ProgressBar

# values and maps from wetterzentrale.de    
values = [ 
	'500hPa Geopot. T °C,Bodendruck',
	'850hPa Geopot. und Temp °C',
	'3h Niederschlag',
	'2m Temperatur [max/min]',
	'10m Wind',
	'CAPE+Lifted Index',
	'700 hPa Vertikalbewegung',
	'2m Taupunkt',
	'850 hPa Aeq.Pot.T + Bodendruck',
	'Bodendruck + Hohe Wolken',
	'Bodendruck + Mittelhohe Wolken',
	'Bodendruck + Tiefe Wolken',
    '700hPa Wind',		
    'Gesamtniederschlag',
	'Spitzenwind']

# regions for wetterzentrale.de   
regions = {
	"M-Europa": "mgfs",
	"Europa" : "tavn",
	"N-Amerika": "namavn",
	"S-Amerika": "samavn",
	"Afrika": "afravn",
	"Ostasien": "oasavn",
	"Südasien": "sasavn",
	"Australien": "ausavn",
	"N-Hemisph.": "havn",
	"S-Hemisph.": "savn",
	"Osttropen": "etavn",
	"Westtropen": "wtavn",
	"Global": "wavn" }

appTitle = "GFS-Viewer (Karten)"
        
class gfsViewerApp(App):
	global values
	global regions

	#init App class
	def __init__(self, **kwargs):
		super(gfsViewerApp, self).__init__(**kwargs)
		
		self.carousel = Carousel(direction='right',anim_move_duration=0.1, anim_type='in_out_sine',loop='false')
		self.active_region = "M-Europa"
		self.active_value = "3h Niederschlag"
		self.last_df = 0
		self.image = []
		self.limit = 0
		self.pb = ""
		self.src = ""

		Loader.start()

	# Loader-complete callback (for some reason AsyncImage got stuck 
	# when fed with to many request at once, so images get loaded here 
	# on after the other..
	def _image_loaded(self, proxyImage):

		if proxyImage.image.texture:
				if len(self.image) > self.loadnum:
					self.image[self.loadnum].texture = proxyImage.image.texture
			
					if (self.loadnum < self.limit):
						self.loadnum = self.loadnum + 1
						self._load_next()				
					self.carousel.canvas.ask_update()
	
	# load next image			
	def _load_next(self,*largs):	
		
		if (self.loadnum < self.limit):
			
			# for some reason to many events where fired, so ignore
			# calls that don't have a unique timestamp
			
			if (len(largs) >0 ):
				if self.last_df == largs[0]:
					ignore = True
				else:
					ignore = False
					self.last_df = largs[0]
			else:
				ignore = False
				
			if not ignore:

				#gif images make trouble, conversion happens on server
				
				src = self.src  %  \
					( regions[self.active_region], ((self.loadnum +1) * self.steps), values.index(self.active_value) + 1)						
			
				proxyImage = Loader.image(src)	
				
				# we already have that image in cache
				if proxyImage.loaded:
					self.image.append(Image())
					self.image[self.loadnum].texture = proxyImage.image.texture
					self.carousel.add_widget(self.image[self.loadnum])
					self.loadnum = self.loadnum + 1
					self._load_next()
					
				# load image in background.						
				else:
					proxyImage.bind(on_load=self._image_loaded)
					self.image.append(Image())
					self.image[self.loadnum].texture = proxyImage.image.texture
					self.carousel.add_widget(self.image[self.loadnum])				
				
				#update widget..
				self.carousel.canvas.ask_update()

		# update progress bar
		self.pb.value =  (self.loadnum) / float(self.limit)  * 100
		self.ltext.text  = "total: + %dh" % ((self.loadnum) * self.steps)

        
	def _load_values(self,*largs):	
		
		if (len(largs) > 0 and self.last_df != 0):
			if self.last_df == largs[0]:
				ignore = True
			else:
				ignore = False
				self.last_df = largs[0]
		else:
			ignore = False

		# for some reason to many events where fired, so ignore
		# calls that don't have a unique timestamp
					
		if not ignore:		
			if self.active_region == "M-Europa":
				self.steps = 3
				self.limit = 60
				
			else:
				self.steps = 6
				self.limit = 30
				
			
			if self.active_region in ["M-Europa","Europa"]:
				self.src = "http://m.ash.to/gfsViewer/imgloader.php?file=R%s%02d%d.gif&type=.png"
			else:
				self.src = "http://www.wetterzentrale.de/pics/R%s%02d%d.png" 
				
			self.loadnum = 0	
			self.image = []
			self.last_df = 0
			self._load_next(*largs)
    
	def _clear_loader(self, *largs):
		Loader.stop()
		self.carousel.clear_widgets()
		self.loadnum = 0	
		self.image = []
		self.pb.value =  0
		self.ltext.text  = "total: "
				
		# now load 
		Clock.schedule_once(self._load_values,0.2)
	
	# new value selected callback	
	def _on_value_select(self,x):
		self.carousel.clear_widgets()
		Clock.schedule_once(self._clear_loader)
		setattr(self.value_button, 'text', x)		
		self.active_value = x
	
	# region select callback		
	def _on_region_select(self,x):
		setattr(self.region_button, 'text', x)
		self.active_region = x
		self._on_value_select(self.active_value)			

	# build layout and app
	def build(self):
		
		self.icon = 'data/icon-s.png'
		self.layout = BoxLayout(orientation='vertical')
		ab = ActionBar(size_hint=(1,0.08), height="48dp")
		av = ActionView()
		av.add_widget(ActionPrevious(title=appTitle,with_previous=False, app_icon=self.icon))
		ab.add_widget(av)
		
		self.layout.add_widget(ab)

		#region_dropdown = DropDown()
		# disable drop-down options for the moment. 
		# needs more work (also different value selectors)
		#for i in regions:
		#	btn = Button(text=i,  size_hint_y=None, height="48dp")
		#	btn.bind(on_release=lambda btn: region_dropdown.select(btn.text))
		#	region_dropdown.add_widget(btn)
		#	region_dropdown.bind(on_select=lambda instance, x: self._on_region_select(x))			
		self.region_button = Button(text=self.active_region, size_hint_y=None, height="48dp")
		#self.region_button.bind(on_release=region_dropdown.open)
		self.layout.add_widget(self.region_button)	
					
		value_dropdown = DropDown()
		
		for i in range(len(values)):
			btn = Button(text=values[i], size_hint_y=None, height="48dp")
			btn.bind(on_release=lambda btn: value_dropdown.select(btn.text))
			value_dropdown.add_widget(btn)
			value_dropdown.bind(on_select=lambda instance, x: self._on_value_select(x))	
		self.value_button = Button(text=self.active_value, size_hint_y=None, height="48dp")
		self.value_button.bind(on_release=value_dropdown.open)
		self.layout.add_widget(self.value_button)		
		
		self.layout.add_widget(self.carousel)
		
		self.pb = ProgressBar(max=100,value=50, size_hint=(1,0.08),height=48)
		self.layout.add_widget(self.pb)
		self.ltext = Label(text='', size_hint_y=None,height="12dp",font_size="10dp")
		self.layout.add_widget(self.ltext)	
		self._on_value_select(self.active_value)
			
		return self.layout
		
if __name__ == '__main__':
    gfsViewerApp().run()
