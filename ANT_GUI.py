#!/usr/bin/env python


#The ambiguous nucleotide tool (ANT) is a free and open source tool aimed at
#generating and analysing degenerate codons to support research in protein engineering, directed evolution and synthetic biology.

#Copyright (C) 2015  Martin Engqvist | 
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#LICENSE:
#This file is part of ANT.
#
#ANT is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License, or
#(at your option) any later version.
# 
#ANT is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Library General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#Get source code at: To be added....
#


import wx
import math
from base_class import ANTBaseDrawingClass
from base_class import ANTBaseClass
import ANT
import dna
import protein
import re
import pyperclip



		
class CodonView(ANTBaseDrawingClass):
	'''
	The codon view class draws a user interface. 
	It also keeps track of mouse events and use those to keep track of user actions.
	The information generated by user actions is used to compute the degenerate codon.
	'''
	def __init__(self, parent, id):

		self.highlighted = False #a variable for keeping track of whether any object is highlighted
		self.codon = False
		self.target = []
		self.possible = []
		self.offtarget = []
		self.AA_count = {}
		self.text_edit_active = False #to keep track of whether text is being edited

		#set up a dictionary to keep track of which color belongs to what object
		self.catalog = {} #for matching features with the unique colors
		self.catalog['(255, 255, 255, 255)'] = False #the background is white, have to add that key
		self.catalog['(-1, -1, -1, 255)'] = False #Seems like on macs the background gives different values
		self.unique_color = (0,0,0)

		#set the initial value of a few variables
		self.xc = 0
		self.yc = 0
		self.table = 1 #codon table

		#initialize
		super(CodonView, self).__init__(parent, wx.ID_ANY)

		#bind basic mouse events to methods
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_MOTION, self.OnMotion)




############ Setting required methods ####################
	
	def update_ownUI(self):
		'''
		This would get called if the drawing needed to change, for whatever reason.

		The idea here is that the drawing is based on some data generated
		elsewhere in the system. If that data changes, the drawing needs to
		be updated.

		This code re-draws the buffer, then calls Update, which forces a paint event.
		'''
		dc = wx.MemoryDC()
		dc.SelectObject(self._Buffer)
		self.Draw(dc)
		dc.SelectObject(wx.NullBitmap) # need to get rid of the MemoryDC before Update() is called.
		self.Refresh()
		self.Update()


############### Done setting required methods #######################


	def Draw(self, dc):
		'''
		Method for drawing stuff on gcdc.
		This method is responsible for drawing the entire user interface, with the exception of buttons. I add those later.
		'''
		
		#################
		self.xc = 850/3 #centre of codon circle in x
		self.yc = 450/2 #centre of codon circle in y
		self.Radius = self.yc/1.2
		self.unique_color = (0,0,0)

		dc.SetBackground(wx.Brush("White"))
		dc.Clear() # make sure you clear the bitmap!
		gcdc = wx.GCDC(dc) #make gcdc from the dc (for use of transparency and antialiasing)

		#make a hidden dc to which features can be drawn in unique colors and later used for hittests. This drawing only exists in memory.
		self.hidden_dc = wx.MemoryDC()
		self.hidden_dc.SelectObject(wx.EmptyBitmap(self.ClientSize[0], self.ClientSize[1]))
		self.hidden_dc.SetBackground(wx.Brush("White"))
		self.hidden_dc.Clear() # make sure you clear the bitmap!

		#set what colors the different fields should have
		target_color = '#CCFF66' #chosen amino acids
		possible_color = '#FFFF66' #amino acid that may still be chosen
		offtarget_color = '#FF9966' #off-target amino acids
		nucleotide_color = '#8B835F' #standard nucleotide color
		coding_nucleotide_color = '#4B4424' #for coloring the nucleotides encoded by the degenerate codon
		line_color = '#000000' #for lines
		first_nuc_background = '#ffe7ab' #background of first nucleotide
		second_nuc_background = '#ffd976' #background of second nucleotide
		third_nuc_background = '#ffc700' #background of third nucleotide
		aa_background = '#FFFFFF' #background color for amino acids
		aa_highlight = '#FF0000' #highlight color for the amino acid that mouse pointer hovers over
		
		#These parameters determine the "thickness" of the nucleotide and amino acid sections
		first_nucleotide_thickness = self.Radius/3.0
		second_nucleotide_thickness = self.Radius/4.5
		third_nucleotide_thickness = self.Radius/10.0
		amino_acid_thickness = self.Radius/3.0

		
		
		###########################
		## draw first nucleotide ##
		###########################
		
		#set parameters
		radius = first_nucleotide_thickness
		thickness = first_nucleotide_thickness
		font = wx.Font(pointSize=self.Radius/6.5, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		gcdc.SetPen(wx.Pen(colour=first_nuc_background, width=1))
		gcdc.SetBrush(wx.Brush(first_nuc_background))
		nucleotides = ['T', 'C', 'A', 'G']
		
		#do the drawing
		for i in range(len(nucleotides)):
			#draw the background
			start_angle = 0 + 90*i
			finish_angle = 90+90*i
			pointlist = self.make_arc(self.xc, self.yc, start_angle, finish_angle, radius, thickness, step=5)
			gcdc.DrawPolygon(pointlist)
			
			#determine text color
			#if nucleotide is part of degenerate codon it should have a different color
			gcdc.SetTextForeground((nucleotide_color))
			if self.codon is not False:
				if nucleotides[i].replace('U','T') in dna.UnAmb(self.codon[0]):
					gcdc.SetTextForeground((coding_nucleotide_color))
			
			#draw the text
			text_extent = gcdc.GetTextExtent(nucleotides[i])
			x1, y1 = self.AngleToPoints(self.xc, self.yc, radius/2, finish_angle-(finish_angle-start_angle)/2) #(centre_x, centre_y, radius, angle)
			gcdc.DrawText(nucleotides[i], x1-text_extent[0]/2, y1-text_extent[1]/2)
			
			

		############################
		## draw second nucleotide ##
		############################
		
		#set parameters
		radius = first_nucleotide_thickness+second_nucleotide_thickness
		thickness = second_nucleotide_thickness
		font_size = self.Radius/12.0
		if font_size < 1:
			print('The problem lies with the self.Radius/12.0. Seems like it is too small.')
			font_size = 10
		font = wx.Font(pointSize=self.Radius/12.0, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		gcdc.SetPen(wx.Pen(colour=second_nuc_background, width=1))
		gcdc.SetBrush(wx.Brush(second_nuc_background))
		nucleotides = ['TT', 'TC', 'TA', 'TG','CT', 'CC', 'CA', 'CG','AT', 'AC', 'AA', 'AG', 'GT', 'GC', 'GA', 'GG']
		
		#do the drawing
		for i in range(len(nucleotides)):
			#draw the background
			start_angle = 0 + 22.5*i
			finish_angle = 22.5+22.5*i
			pointlist = self.make_arc(self.xc, self.yc, start_angle, finish_angle, radius, thickness, step=0.5)
			gcdc.DrawPolygon(pointlist)
			
			#determine text color
			#if nucleotide is part of degenerate codon it should have a different color
			gcdc.SetTextForeground((nucleotide_color))
			if self.codon is not False:
				if nucleotides[i].replace('U','T') in dna.UnAmb(self.codon[0:2]):
					gcdc.SetTextForeground((coding_nucleotide_color))
			
			#draw the text
			text_extent = gcdc.GetTextExtent(nucleotides[i][1])
			x1, y1 = self.AngleToPoints(self.xc, self.yc, first_nucleotide_thickness+second_nucleotide_thickness/2, finish_angle-(finish_angle-start_angle)/2)
			gcdc.DrawText(nucleotides[i][1], x1-text_extent[0]/2, y1-text_extent[1]/2)


			
		###########################			
		## draw third nucleotide ##
		###########################
		
		#set parameters
		radius = first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness
		thickness = third_nucleotide_thickness
		font = wx.Font(pointSize=self.Radius/28.0, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		gcdc.SetPen(wx.Pen(colour=third_nuc_background, width=1))
		gcdc.SetBrush(wx.Brush(third_nuc_background))
		codons = ['TTT', 'TTC', 'TTA', 'TTG','TCT', 'TCC', 'TCA', 'TCG','TAT', 'TAC', 'TAA', 'TAG', 'TGT', 'TGC', 'TGA', 'TGG',\
					'CTT', 'CTC', 'CTA', 'CTG','CCT', 'CCC', 'CCA', 'CCG','CAT', 'CAC', 'CAA', 'CAG', 'CGT', 'CGC', 'CGA', 'CGG',\
					'ATT', 'ATC', 'ATA', 'ATG','ACT', 'ACC', 'ACA', 'ACG','AAT', 'AAC', 'AAA', 'AAG', 'AGT', 'AGC', 'AGA', 'AGG',\
					'GTT', 'GTC', 'GTA', 'GTG','GCT', 'GCC', 'GCA', 'GCG','GAT', 'GAC', 'GAA', 'GAG', 'GGT', 'GGC', 'GGA', 'GGG']
					
		#do the drawing
		for i in range(len(codons)):
			#draw the background
			start_angle = 0 + 5.625*i
			finish_angle = 5.625+5.625*i
			pointlist = self.make_arc(self.xc, self.yc, start_angle, finish_angle, radius, thickness, step=0.1)
			gcdc.DrawPolygon(pointlist)
			
			#determine text color
			#if nucleotide is part of degenerate codon it should have a different color
			gcdc.SetTextForeground((nucleotide_color))
			if self.codon is not False:
				if codons[i].replace('U','T') in dna.UnAmb(self.codon):
					gcdc.SetTextForeground((coding_nucleotide_color))
			
			#draw the text
			text_extent = gcdc.GetTextExtent(codons[i][2])
			x1, y1 = self.AngleToPoints(self.xc, self.yc, first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness/2, finish_angle-(finish_angle-start_angle)/2)
			gcdc.DrawText(codons[i][2], x1-text_extent[0]/2, y1-text_extent[1]/2)

			
			
		############################################
		## draw the amino acid segments and names ##	
		############################################		
			
		#set parameters 
		radius = first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness+amino_acid_thickness
		thickness = amino_acid_thickness
		font = wx.Font(pointSize=self.Radius/22.0, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		gcdc.SetTextForeground(('#000000'))
		finish_angle = 0
		
		#do the drawing
		AA_width = 0
		current_AA = dna.Translate(codons[0], self.table)
		for codon in codons:
			AA = dna.Translate(codon, self.table)
			if codon == 'GGG': #catch the last codon
				AA_width += 1
				AA = None
				
			if current_AA == AA:
				AA_width += 1
			else:
				#draw the amino acid segments
				gcdc.SetPen(wx.Pen(colour=aa_background, width=0))
				if current_AA in self.target: #if current AA is a selected one
					gcdc.SetPen(wx.Pen(colour=target_color, width=0))
					gcdc.SetBrush(wx.Brush(target_color))
				elif current_AA in self.offtarget: #if it is in the off-targets list
					gcdc.SetPen(wx.Pen(colour=offtarget_color, width=0))
					gcdc.SetBrush(wx.Brush(offtarget_color))
				elif current_AA in self.possible: #if current AA is among the ones that may be selected without further off-targets
					gcdc.SetPen(wx.Pen(colour=possible_color, width=0))
					gcdc.SetBrush(wx.Brush(possible_color))
				else:									#otherwise use standard color
					gcdc.SetBrush(wx.Brush(aa_background))
				start_angle = finish_angle
				finish_angle = start_angle+5.625*AA_width
				pointlist = self.make_arc(self.xc, self.yc, start_angle, finish_angle, radius, thickness, step=0.1)
				gcdc.DrawPolygon(pointlist)

				#draw hidden color which is used for hittests
				self.catalog[str(self.NextRGB()+(255,))] = current_AA

				self.hidden_dc.SetPen(wx.Pen(colour=self.unique_color, width=0))
				self.hidden_dc.SetBrush(wx.Brush(colour=self.unique_color))
				self.hidden_dc.DrawPolygon(pointlist)			

				#draw lines
				angle = start_angle
				gcdc.SetPen(wx.Pen(colour=line_color, width=1))
				if angle in [0,90,180,270]:
					radius = 0
				elif angle % 22.5 == 0:
					radius = first_nucleotide_thickness
				elif angle % 5.625 ==0:
					radius = first_nucleotide_thickness+second_nucleotide_thickness
				x1, y1 = self.AngleToPoints(self.xc, self.yc, radius, angle)
				radius = radius = first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness+amino_acid_thickness
				x2, y2 = self.AngleToPoints(self.xc, self.yc, radius, angle)
				gcdc.DrawLine(x1, y1, x2, y2)

				#draw amino acid text
				text_angle = finish_angle-(finish_angle-start_angle)/2

				if finish_angle <= 180:
					text_extent = gcdc.GetTextExtent(protein.one_to_three(current_AA)+' (%s)' % current_AA)
					text_radius = (first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness)*1.05

					#need to adjust for text height. Imagine right angled triangle. Adjecent is radius. Opposite is half of the text height. Calculate tan angle.
					tanangle = (0.5*text_extent[1])/text_radius #calculate the Tan(angle)
					radians = math.atan(tanangle) #negate the Tan part and get radians
					degrees = radians*(180/math.pi)	#convert radians to degrees
					text_position_angle = text_angle-degrees			

					tx, ty = self.AngleToPoints(self.xc, self.yc, text_radius, text_position_angle)
					gcdc.DrawRotatedText(protein.one_to_three(current_AA)+' (%s)' % current_AA, tx, ty, -text_angle+90)
				else:
					text_extent = gcdc.GetTextExtent(protein.one_to_three(current_AA)+' (%s)' % current_AA)
					text_radius = (first_nucleotide_thickness+second_nucleotide_thickness+third_nucleotide_thickness)*1.05 + text_extent[0]

					#need to adjust for text height. Imagine right angled triangle. Adjacent is radius. Opposite is half of the text height. Calculate tan angle.
					tanangle = (0.5*text_extent[1])/text_radius #calculate the Tan(angle)
					radians = math.atan(tanangle) #negate the Tin part and get radians
					degrees = radians*(180/math.pi)	#convert radians to degrees
					text_position_angle = text_angle+degrees			

					tx, ty = self.AngleToPoints(self.xc, self.yc, text_radius, text_position_angle)
					gcdc.DrawRotatedText(protein.one_to_three(current_AA)+' (%s)' % current_AA, tx, ty, -text_angle-90)

				#now re-set the parameters for the next round
				current_AA = AA
				AA_width = 1
		
		
		###########################################################################
		## draw the highlighted amino acid (the one that the mouse hovers above) ##
		###########################################################################
		
		gcdc.SetPen(wx.Pen(colour=aa_highlight, width=1))
		gcdc.SetBrush(wx.Brush(colour=(0,0,0,0))) #transparent

		finish_angle = 0
		start_angle = 0		
		AA_width = 0
		current_AA = dna.Translate(codons[0], self.table)
		for codon in codons:
			AA = dna.Translate(codon, self.table)
			if codon == 'GGG': #catch the last codon
				AA_width += 1
				AA = None
				
			if current_AA == AA:
				AA_width += 1
			else:
				#if current AA is highlighted, redraw that segment with a different pen
				finish_angle = start_angle+5.625*AA_width
				if current_AA == self.highlighted: #if highlighted AA is the current one
					pointlist = self.make_arc(self.xc, self.yc, start_angle, finish_angle, radius, thickness, step=0.1)
					gcdc.DrawPolygon(pointlist)
				start_angle = finish_angle
				current_AA = AA
				AA_width = 1
				
			
			
		###############################
		## Draw the degenerate codon ##
		###############################
		
		#write what the degenerate codon is 
		point_size = int(self.Radius/8)
		font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.ITALIC, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground((line_color))
		x = 850*0.62
		y = 450*0.08
		text = 'Codon:'
		gcdc.DrawText(text, x, y)

		x = 850*0.75
		point_size = int(self.Radius/6)
		font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground((coding_nucleotide_color))
		
		if self.codon is False:
			text = ''
		else:
			text = self.codon
		gcdc.DrawText(text, x, y)

		
		#below the degenerate codon, list the bases it codes for
		if self.codon is not False:
			#get text position based on the ambigous codon
			first_x = x + gcdc.GetTextExtent(text[0:1])[0] - gcdc.GetTextExtent(text[0])[0]/2
			second_x = x + gcdc.GetTextExtent(text[0:2])[0] - gcdc.GetTextExtent(text[1])[0]/2
			third_x = x + gcdc.GetTextExtent(text[0:3])[0] - gcdc.GetTextExtent(text[2])[0]/2
			start_y = y + gcdc.GetTextExtent(text[0])[1]

			#set new text size
			point_size = int(self.Radius/18)
			font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTSTYLE_ITALIC, weight=wx.FONTWEIGHT_NORMAL)
			gcdc.SetFont(font)
			gcdc.SetTextForeground((coding_nucleotide_color))

			first = dna.UnAmb(self.codon[0])
			second = dna.UnAmb(self.codon[1])
			third = dna.UnAmb(self.codon[2])

			first_y = start_y
			for i in range(0, len(first)):
				text = first[i]
				#adjust for the size of that text
				pos_x = first_x - gcdc.GetTextExtent(text)[0]/2
				gcdc.DrawText(text, pos_x, first_y)
				first_y += point_size*1.2

			second_y = start_y
			for i in range(0, len(second)):
				text = second[i]
				#adjust for the size of that text
				pos_x = second_x - gcdc.GetTextExtent(text)[0]/2
				gcdc.DrawText(text, pos_x, second_y)
				second_y += point_size*1.2

			third_y = start_y
			for i in range(0, len(third)):
				text = third[i]
				#adjust for the size of that text
				pos_x = third_x - gcdc.GetTextExtent(text)[0]/2
				gcdc.DrawText(text, pos_x, third_y)
				third_y += point_size*1.2

				
				
		##############		
		## draw key	##
		##############
		
		width = self.Radius/16
		height = self.Radius/16
		
		point_size = int(self.Radius/20)
		font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground(('#666666'))

		#target AA key
		text = 'Target AA'
		x = 10
		y = 10
		gcdc.SetBrush(wx.Brush(target_color))
		gcdc.SetPen(wx.Pen(colour='#666666', width=0))
		gcdc.DrawRectangle(x, y, width, height)
		gcdc.DrawText(text, x+width*1.2, y)

		#possible AA key
		text = 'Possible AA'
		x = 10
		y += point_size*1.5
		gcdc.SetBrush(wx.Brush(possible_color))
		gcdc.SetPen(wx.Pen(colour='#E6E65C', width=1))
		gcdc.DrawRectangle(x, y, width, height)
		gcdc.DrawText(text, x+width*1.2, y)

		#off-target AA key
		text = 'Off-target AA'
		x = 10
		y += point_size*1.5
		gcdc.SetBrush(wx.Brush(offtarget_color))
		gcdc.SetPen(wx.Pen(colour='#666666', width=0))
		gcdc.DrawRectangle(x, y, width, height)
		gcdc.DrawText(text, x+width*1.2, y)

		
		
		################
		## draw graph ##
		################
		
		AA_order = ('A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y', '*', 'U')
		AA_full = {'F':'Phenylalanine', 'L':'Leucine', 'S':'Serine', 'Y':'Tyrosine', '*':'Stop', 'C':'Cysteine', 'stop2':'Stop', 'W':'Tryptophan', 'L2':'Leucine', 'P':'Proline', 'H':'Histidine', 'Q':'Glutamine', 'R':'Arginine', 'I':'Isoleucine', 'M':'Methionine', 'T':'Threonine', 'N':'Asparagine', 'K':'Lysine', 'S2':'Serine', 'R2':'Arginine', 'V':'Valine', 'A':'Alanine', 'D':'Aspartic acid', 'E':'Glutamic acid', 'G':'Glycine', 'U':'Unnatural AA'}

		originx = 850*0.75 #centre of plot in x
		originy = 450*0.4 #centre of plot in y
		sizex = 850*0.2
		sizey = 450*0.55

		xspacing = sizex/7
		yspacing = float(sizey)/float(22)
		tick_size = sizex/30
		
		#draw background rectangle
		gcdc.SetBrush(wx.Brush("#fff2d1"))
		gcdc.SetPen(wx.Pen(colour=line_color, width=0))
		gcdc.DrawRectangle(originx, originy, sizex, sizey)

		#title
		point_size = int(sizex/15)
		font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground((line_color))
		title = 'Codon count for each AA'
		gcdc.DrawText(title, originx, originy-gcdc.GetTextExtent(text)[1]*2)

		#y labels (amino acids)		
		point_size = int(self.Radius/23.0)
		font = wx.Font(pointSize=point_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground((line_color))
		for i in range(0, 22):	
			amino_acid = '%s(%s)' % (protein.one_to_three(AA_order[i]), AA_order[i])
			gcdc.DrawText(amino_acid, originx-gcdc.GetTextExtent(amino_acid)[0]-tick_size, originy+(yspacing*i+yspacing/2.0)-gcdc.GetTextExtent(amino_acid)[1]/2)

		#x labels (count)
		for i in range(1, 7):	
			gcdc.DrawText(str(i), originx+xspacing*i-gcdc.GetTextExtent('6')[0]/2, originy-gcdc.GetTextExtent('6')[1]-tick_size/2.0)	

		#x ticks
		for i in range(1, 7):
			gcdc.DrawLine(originx+(xspacing*i), originy, originx+(xspacing*i), originy+tick_size)
			gcdc.DrawLine(originx+(xspacing*i), originy+sizey, originx+(xspacing*i), originy+sizey-tick_size)

#		#y ticks
		for i in range(1, 22):
			gcdc.DrawLine(originx, originy+(yspacing*i), originx+tick_size, originy+(yspacing*i))
			gcdc.DrawLine(originx+sizex, originy+(yspacing*i), originx+sizex-tick_size, originy+(yspacing*i))

		#draw bars according to how many times each AA is encoded
		if self.codon is not False:
			for i in range(0, 22):	
				AA = AA_order[i]
				if AA in self.target: #if current AA is a selected one
					gcdc.SetBrush(wx.Brush(target_color))
				elif AA in self.offtarget: #if it is in the off-targets list
					gcdc.SetBrush(wx.Brush(offtarget_color))
				else:	
					gcdc.SetBrush(wx.Brush('#666666'))

				count = self.AA_count[AA]
				gcdc.DrawRectangle(originx, originy+yspacing*i+yspacing*0.1, count*xspacing, yspacing*0.8) #(x, y, w, h)




##############################################################

	def HitTest(self):
		'''
		Tests whether the mouse is over any amino acid field.
		'''
		dc = wx.ClientDC(self) #get the client dc
		x, y = self.ScreenToClient(wx.GetMousePosition()) #get coordinate of mouse event
		pixel_color = self.hidden_dc.GetPixel(x,y) #use that coordinate to find pixel on the hidden dc
		return self.catalog[str(pixel_color)] #return the amino acid


	def OnLeftUp(self, event):
		'''
		When the depressed left mouse button is released, determine whether the mouse was above an amino acid field. 
		If it was, append that amino acid to the list of chosen amino acids. 
		If the amino acid was already chosen, then remove it from the selection.
		'''
		amino_acid = self.HitTest()
		if amino_acid is not False:
			if amino_acid not in self.target:
				self.target.append(amino_acid)
			elif amino_acid in self.target:
				self.target.remove(amino_acid)
			else:
				raise ValueError

		if len(self.target)>0:
			codon_object = ANT.DegenerateCodon(self.target, self.table)
			self.codon = codon_object.getTriplet()
			self.target = codon_object.getTarget()
			self.offtarget = codon_object.getOffTarget()
			self.possible = codon_object.getPossible()
			self.AA_count = codon_object.getCodonsPerAA()
			self.report = codon_object.getReport()
		else:
			self.codon = False
			self.offtarget = []
			self.possible = []
		
		#update drawing
		self.update_ownUI()


	def OnMotion(self, event):
		'''
		When mouse is moved, test whether it hovers above an amino acid field.
		'''
		amino_acid = self.HitTest()
		
		if amino_acid is not self.highlighted: #if the index did not change
			self.highlighted = amino_acid
			
			#update drawing
			self.update_ownUI()





#make new class and add in buttons and the codon wheel view			
class CodonButtonWrapper(ANTBaseClass):
	'''
	This class is intended to glue together the plasmid drawing with control buttons.
	'''
	def __init__(self, parent, id):
		ANTBaseClass.__init__(self, parent, id)
		self.codon_view = CodonView(self, -1)	
		
		#buttons
		reset = wx.Button(self, 1, 'Reset')		
		self.evaluate = wx.Button(self, 5, 'Evaluate Codon')
		self.evaluate.Disable() #disable the button by default
		self.copy = wx.Button(self, 6, 'Copy to Clipboard')		
		
		#the combobox
		options = ["1: Standard Code",
					"2: Vertebrate Mitochondrial Code",
					"3: Yeast Mitochondrial Code",
					"4: Mold, Protozoan, Coelenterate Mitochondrial Code",
					"5: Invertebrate Mitochondrial Code",
					"6: Ciliate, Dasycladacean and Hexamita Nuclear Code",
					"9: Echinoderm and Flatworm Mitochondrial Code",
					"10: Euplotid Nuclear Code",
					"11: Bacterial, Archaeal and Plant Plastid Code",
					"12: Alternative Yeast Nuclear Code",
					"13: Ascidian Mitochondrial Code",
					"14: Alternative Flatworm Mitochondrial Code",
					"15: Blepharisma Nuclear Code",
					"16: Chlorophycean Mitochondrial Code",
					"21: Trematode Mitochondrial Code",
					"22: Scenedesmus obliquus mitochondrial Code",
					"23: Thraustochytrium Mitochondrial Code",
					"24: Pterobranchia mitochondrial Code",
					"25: Candidate Division SR1 and Gracilibacteria Code",
					"1001: Standard Code With UAG Codon Reassignment"]
		self.combobox = wx.ComboBox(self, id=2, size=(-1, -1), choices=options, style=wx.CB_READONLY)
		self.combobox.Select(0)
		
		#text input field
		self.input_codon = wx.TextCtrl(self, id=4, size=(50,-1), style=wx.TE_RICH)

		#bind actions to buttons, text field and combobox
		self.Bind(wx.EVT_BUTTON, self.OnReset, id=1)
		self.Bind(wx.EVT_COMBOBOX, self.OnComboboxSelect, id=2)
		self.Bind(wx.EVT_TEXT, self.InputCodonOnText, id=4)		
		self.Bind(wx.EVT_BUTTON, self.OnEvaluate, id=5)
		self.Bind(wx.EVT_BUTTON, self.OnCopy, id=6)
		
		#arrange buttons, text field and combobox vertically		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(item=reset)
		sizer.Add(item=self.combobox)
		sizer.Add(item=self.input_codon, flag=wx.LEFT, border=50)
		sizer.Add(item=self.evaluate)
		sizer.Add(item=self.copy, flag=wx.LEFT, border=50)

		#add buttons on top and the codon wheel on the bottom
		sizer2 = wx.BoxSizer(wx.VERTICAL)
		sizer2.Add(item=sizer, proportion=0, flag=wx.EXPAND)
		sizer2.Add(item=self.codon_view, proportion=-1, flag=wx.EXPAND)

		self.SetSizer(sizer2)

	
	def update_ownUI(self):
		'''
		User interface updates by redrawing the codon wheel, associated graph and displayed codon.
		'''
		self.codon_view.update_ownUI()
		
			
	def OnReset(self, evt):
		'''
		When reset button is clicked, remove all chosen amino acids.
		'''
		self.codon_view.codon = False
		self.codon_view.target = []
		self.codon_view.offtarget = []
		self.codon_view.possible = []
		self.codon_view.report = ''
		
		#update drawing
		self.update_ownUI()
		
	def OnComboboxSelect(self, evt):
		'''
		When a codon table is chosen from the combobox, generate a new codon object, update parameters and update drawing.
		'''
		self.codon_view.table = self.combobox.GetValue().split(':')[0]

		#compute result with new table
		if len(self.codon_view.target)>0:
			codon_object = ANT.DegenerateCodon(self.codon_view.target, self.codon_view.table)
			self.codon_view.codon = codon_object.getTriplet()
			self.codon_view.target = codon_object.getTarget()
			self.codon_view.offtarget = codon_object.getOffTarget()
			self.codon_view.possible = codon_object.getPossible()
			self.codon_view.AA_count = codon_object.getCodonsPerAA()
			self.codon_view.report = codon_object.getReport()
		#update drawing
		self.update_ownUI()

	
	def InputCodonOnText(self, evt):
		'''
		When text is entered into the text field, check if it is a valid degenerate codon.
		The validity of the codon affects the text color and whether the "Evaluate" button is activated or not.
		'''
		codon = str(self.input_codon.GetLineText(0)).upper() #get the input codon
	
		#if it is a valid codon, make text black and activate enable button. If not, red text and disabled button.
		m = re.match('^[GATCRYWSMKHBVDN]{3}$', codon)
		if m != None:
			self.input_codon.SetForegroundColour(wx.BLACK)
			self.evaluate.Enable()
		elif m == None:
			self.input_codon.SetForegroundColour(wx.RED)
			self.evaluate.Disable()
			
			
	def OnEvaluate(self, evt):
		'''
		When the evaluate button is pressed, compute which amino acids it encodes and update drawing.
		'''
		#make a codon object with the codon and then set parameters accordingly
		codon_object = ANT.DegenerateCodon(str(self.input_codon.GetLineText(0)).upper(), self.codon_view.table)
		self.codon_view.codon = codon_object.getTriplet()
		self.codon_view.target = codon_object.getTarget()
		self.codon_view.offtarget = codon_object.getOffTarget()
		self.codon_view.possible = codon_object.getPossible()	
		self.codon_view.AA_count = codon_object.getCodonsPerAA()
		self.codon_view.report = codon_object.getReport()
		
		#update drawing
		self.update_ownUI()

		
	def OnCopy(self, evt):
		'''
		Copy a report to the clipboard.
		'''
		if self.codon_view.codon is False:
			pyperclip.copy('No selection has been made.')
		else:
			pyperclip.copy(self.codon_view.report)
		
		
##### main loop
class MyApp(wx.App):
	def OnInit(self):
		frame = wx.Frame(None, -1, title="ANT", size=(900,500))
		panel =	CodonButtonWrapper(frame, -1)
		frame.Centre()
		frame.Show(True)
		self.SetTopWindow(frame)
		return True


if __name__ == '__main__': #if script is run by itself and not loaded	
	app = MyApp(0)
	app.MainLoop()
